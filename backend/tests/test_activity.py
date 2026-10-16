from datetime import UTC, datetime, timedelta

import httpx
import respx

from app.services.smartsheet import client as client_module
from tests.conftest import writes
from tests.factories import OWNER_EMAIL, SHEET_ID, share_json, sheet_json

SHEET = f"/sheets/{SHEET_ID}"
PRIMARY = "900"
OTHER = "901"


def iso(days_ago: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def row(row_id: str, editor: str, days_ago: float, label: str = "Tarea") -> dict:
    return {
        "id": int(row_id),
        "rowNumber": int(row_id) % 1000,
        "cells": [{"columnId": int(PRIMARY), "value": label, "displayValue": label}],
        "createdAt": iso(400),
        "createdBy": {"email": OWNER_EMAIL, "name": "Dueña"},
        "modifiedAt": iso(days_ago),
        "modifiedBy": {"email": editor, "name": editor.split("@")[0]},
    }


def mock_sheet(smartsheet: respx.MockRouter, rows: list[dict], page_size: int = 500) -> None:
    smartsheet.get(f"{SHEET}/columns").respond(
        json={
            "totalPages": 1,
            "data": [
                {"id": int(PRIMARY), "title": "Tarea", "index": 0, "primary": True},
                {"id": int(OTHER), "title": "Estado", "index": 1},
            ],
        }
    )

    def sheet(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("include") != "writerInfo":
            return httpx.Response(200, json=sheet_json())
        page = int(request.url.params["page"])
        chunk = rows[(page - 1) * page_size : page * page_size]
        return httpx.Response(200, json=sheet_json() | {"totalRowCount": len(rows), "rows": chunk})

    smartsheet.get(SHEET).mock(side_effect=sheet)
    smartsheet.get("/shares").respond(
        json={
            "items": [
                share_json("O", OWNER_EMAIL, "OWNER"),
                share_json("A", "ana@example.com", "EDITOR"),
                share_json("L", "luis@example.com", "ADMIN"),
            ]
        }
    )


async def test_changed_rows_by_period(client, smartsheet) -> None:
    rows = [
        row("1001", "ana@example.com", 2),
        row("1002", "ana@example.com", 1),
        row("1003", "ex@example.com", 50),
    ]
    mock_sheet(smartsheet, rows)
    body = (await client.get(f"/api/sheets/{SHEET_ID}/activity", params={"days": 30})).json()
    assert body["rows_total"] == 3 and body["changed_rows_total"] == 2
    assert [r["row_id"] for r in body["changed_rows"]] == ["1002", "1001"]
    assert body["changed_rows"][0]["label"] == "Tarea"
    assert body["limitations"]
    assert writes(smartsheet) == []


async def test_editors_with_current_level(client, smartsheet) -> None:
    rows = [row("1001", "ana@example.com", 1), row("1002", "ex@example.com", 3)]
    mock_sheet(smartsheet, rows)
    body = (await client.get(f"/api/sheets/{SHEET_ID}/activity")).json()
    editors = {e["email"]: e for e in body["editors"]}
    assert editors["ana@example.com"]["access_level"] == "EDITOR"
    assert editors["ex@example.com"]["access_level"] is None  # ya no tiene la hoja compartida
    assert [i["email"] for i in body["idle_editors"]] == ["luis@example.com"]


async def test_rows_are_paginated(client, smartsheet, monkeypatch) -> None:
    rows = [row(str(2000 + n), "ana@example.com", 1) for n in range(5)]
    mock_sheet(smartsheet, rows, page_size=2)
    monkeypatch.setattr(client_module, "_ROWS_PAGE", 2)
    body = (await client.get(f"/api/sheets/{SHEET_ID}/activity")).json()
    assert body["rows_total"] == 5
    pages = [
        call.request.url.params.get("page")
        for call in smartsheet.calls
        if call.request.url.params.get("include") == "writerInfo"
    ]
    assert pages == ["1", "2", "3"]


async def test_row_history_all_columns(client, smartsheet) -> None:
    mock_sheet(smartsheet, [])
    smartsheet.get(f"{SHEET}/rows/1001").respond(
        json={
            "id": 1001,
            "cells": [
                {"columnId": int(PRIMARY), "value": "x"},
                {"columnId": int(OTHER), "value": "Listo"},
                {"columnId": 902},
            ],
        }
    )
    smartsheet.get(f"{SHEET}/rows/1001/columns/{PRIMARY}/history").respond(
        json={
            "totalPages": 1,
            "data": [
                {
                    "columnId": int(PRIMARY),
                    "value": "x",
                    "modifiedAt": iso(5),
                    "modifiedBy": {"email": "ana@example.com"},
                }
            ],
        }
    )
    smartsheet.get(f"{SHEET}/rows/1001/columns/{OTHER}/history").respond(500)
    body = (await client.get(f"/api/sheets/{SHEET_ID}/rows/1001/history")).json()
    assert body["columns_checked"] == 2 and body["failed_columns"] == 1
    assert [(c["column_title"], c["modified_by"]["email"]) for c in body["changes"]] == [
        ("Tarea", "ana@example.com")
    ]
    assert writes(smartsheet) == []


async def test_unknown_column_is_404(client, smartsheet) -> None:
    mock_sheet(smartsheet, [])
    response = await client.get(
        f"/api/sheets/{SHEET_ID}/rows/1001/history", params={"column_id": "7"}
    )
    assert response.json()["detail"]["code"] == "COLUMN_NOT_FOUND"
