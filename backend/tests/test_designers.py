import httpx
import respx

from tests.conftest import writes
from tests.factories import OWNER_EMAIL, SHEET_ID, page, share_json, sheet_json

OTHER_ID = "2222222222222222"
COLUMNS = {
    "totalPages": 1,
    "data": [
        {"id": 1, "title": "Primary", "index": 0, "primary": True},
        {"id": 10, "title": "Designer1", "index": 1},
        {"id": 11, "title": "Designer2", "index": 2},
        {"id": 12, "title": "Project Status", "index": 3},
    ],
}


def row(n: int, d1: str | None, d2: str | None, status: str | None) -> dict:
    cells = [{"columnId": 1, "value": f"F{n}"}, {"columnId": 10, "value": d1}]
    cells += [{"columnId": 11, "value": d2}, {"columnId": 12, "value": status}]
    return {"id": 100 + n, "rowNumber": n, "cells": cells}


def mock(smartsheet: respx.MockRouter) -> None:
    smartsheet.get("/sheets").respond(json=page([sheet_json(), sheet_json(OTHER_ID, "Plan 2025")]))
    data = {
        SHEET_ID: [
            row(1, "Ana Pérez", None, "2. Design Process"),
            row(2, "Ana Pérez", "ana perez", "2. Design on Hold"),
            row(3, "Luis", None, "COMPLETE"),
            row(4, None, None, "1. Survey Progress"),
            row(5, "Designer1", "Designer2", None),
        ],
        OTHER_ID: [row(1, "Ana Pérez", None, "4. Permit Process")],
    }
    shares = {
        SHEET_ID: [
            share_json("O", OWNER_EMAIL, "OWNER"),
            share_json("A", "ana@example.com", "EDITOR", name="Ana Perez"),
        ],
        OTHER_ID: [share_json("O2", OWNER_EMAIL, "OWNER")],
    }
    for sheet_id, sheet_rows in data.items():
        smartsheet.get(f"/sheets/{sheet_id}/columns").respond(json=COLUMNS)

        def respond(
            request: httpx.Request, sheet_rows=sheet_rows, sheet_id=sheet_id
        ) -> httpx.Response:
            return httpx.Response(
                200,
                json=sheet_json(sheet_id) | {"totalRowCount": len(sheet_rows), "rows": sheet_rows},
            )

        smartsheet.get(f"/sheets/{sheet_id}").mock(side_effect=respond)
    smartsheet.get("/shares").mock(
        side_effect=lambda request: httpx.Response(
            200, json={"items": shares[request.url.params["assetId"]]}
        )
    )


async def test_workload_and_access(client, smartsheet) -> None:
    mock(smartsheet)
    body = (await client.get("/api/designers")).json()
    ana = body["designers"][0]
    assert ana["name"] == "Ana Pérez" and ana["person"]["email"] == "ana@example.com"
    assert (ana["open"], ana["on_hold"], ana["closed"]) == (2, 1, 0)
    assert ana["by_phase"] == {"2": 2, "4": 1}
    access = {s["sheet_id"]: s["has_access"] for s in ana["sheets"]}
    assert access == {SHEET_ID: True, OTHER_ID: False}
    assert ana["sheets_without_access"] == 1
    luis = next(d for d in body["designers"] if d["name"] == "Luis")
    assert (luis["closed"], luis["person"], luis["sheets"][0]["has_access"]) == (1, None, None)
    assert body["header_like_rows"] == 1
    assert body["sheet_gaps"] == [
        {
            "sheet_id": SHEET_ID,
            "sheet_name": "Plan 2026",
            "open_without_designer": 1,
            "without_status": 0,
        }
    ]
    assert writes(smartsheet) == []


async def test_closed_statuses_can_be_overridden(client, smartsheet) -> None:
    mock(smartsheet)
    body = (
        await client.get("/api/designers", params={"closed_status": ["4. Permit Process"]})
    ).json()
    ana = body["designers"][0]
    assert (ana["open"], ana["closed"]) == (1, 1)
