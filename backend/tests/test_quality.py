import httpx
import respx

from tests.conftest import writes
from tests.factories import SHEET_ID, sheet_json

SHEET = f"/sheets/{SHEET_ID}"
COLUMNS = [
    {"id": 1, "title": "Tarea", "index": 0, "primary": True, "type": "TEXT_NUMBER"},
    {"id": 2, "title": "Record ID", "index": 1, "type": "TEXT_NUMBER"},
    {"id": 3, "title": "Designer1", "index": 2, "type": "PICKLIST"},
    {"id": 4, "title": "Notas", "index": 3, "type": "TEXT_NUMBER"},
]


def cell(column: int, value: str | None) -> dict:
    return {"columnId": column, "value": value, "displayValue": value}


def mock(smartsheet: respx.MockRouter) -> respx.Route:
    smartsheet.get(f"{SHEET}/columns").respond(json={"totalPages": 1, "data": COLUMNS})
    rows = [
        {"id": 11, "rowNumber": 1, "cells": [cell(1, "A"), cell(2, "10521"), cell(3, "Ana")]},
        {"id": 12, "rowNumber": 2, "cells": [cell(1, "B"), cell(2, "10521"), cell(3, None)]},
        {"id": 13, "rowNumber": 3, "cells": [cell(1, "C"), cell(2, "X-9"), cell(3, "Luis")]},
    ]

    def sheet(request: httpx.Request) -> httpx.Response:
        if "columnIds" not in request.url.params:
            return httpx.Response(200, json=sheet_json())
        return httpx.Response(200, json=sheet_json() | {"totalRowCount": 3, "rows": rows})

    return smartsheet.get(SHEET).mock(side_effect=sheet)


async def test_reads_only_needed_columns(client, smartsheet) -> None:
    route = mock(smartsheet)
    params = {"unique": "record id", "required": "Designer1"}
    body = (await client.get(f"/api/sheets/{SHEET_ID}/quality", params=params)).json()
    checks = {c["check"]: c for c in body["checks"]}
    assert checks["unique"]["issues"][0]["value"] == "10521"
    assert [r["label"] for r in checks["unique"]["issues"][0]["rows"]] == ["A", "B"]
    assert checks["required"]["issues_count"] == 1
    assert route.calls.last.request.url.params["columnIds"] == "1,2,3"
    assert writes(smartsheet) == []


async def test_pattern_and_invalid_regex(client, smartsheet) -> None:
    mock(smartsheet)
    ok = await client.get(f"/api/sheets/{SHEET_ID}/quality", params={"pattern": r"Record ID=^\d+$"})
    (check,) = ok.json()["checks"]
    assert [i["value"] for i in check["issues"]] == ["X-9"]
    bad = await client.get(f"/api/sheets/{SHEET_ID}/quality", params={"pattern": "Record ID=("})
    assert bad.json()["detail"]["code"] == "INVALID_PATTERN"


async def test_errors(client, smartsheet) -> None:
    mock(smartsheet)
    none = await client.get(f"/api/sheets/{SHEET_ID}/quality")
    assert none.json()["detail"]["code"] == "NO_CHECKS"
    unknown = await client.get(f"/api/sheets/{SHEET_ID}/quality", params={"unique": "Recrd ID"})
    detail = unknown.json()["detail"]
    assert detail["code"] == "COLUMN_NOT_FOUND" and "Record ID" in detail["message"]


async def test_columns_endpoint(client, smartsheet) -> None:
    mock(smartsheet)
    columns = (await client.get(f"/api/sheets/{SHEET_ID}/columns")).json()
    assert [c["title"] for c in columns] == ["Tarea", "Record ID", "Designer1", "Notas"]
    assert columns[0]["primary"] is True
