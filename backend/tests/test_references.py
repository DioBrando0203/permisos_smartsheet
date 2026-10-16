import httpx
import respx

from tests.conftest import writes
from tests.factories import SHEET_ID, page, sheet_json

CATALOG_ID = "4444444444444444"
OTHER_ID = "2222222222222222"
NO_COLUMN_ID = "5555555555555555"


def columns(*titles: str) -> dict:
    data = [{"id": 1, "title": "Primary", "index": 0, "primary": True}]
    data += [{"id": 10 + n, "title": t, "index": n + 1} for n, t in enumerate(titles)]
    return {"totalPages": 1, "data": data}


def rows(*designers: str | None) -> list[dict]:
    return [
        {
            "id": 100 + n,
            "rowNumber": n + 1,
            "cells": [{"columnId": 1, "value": f"F{n}"}, {"columnId": 10, "value": d}],
        }
        for n, d in enumerate(designers)
    ]


def mock(smartsheet: respx.MockRouter) -> None:
    smartsheet.get("/sheets").respond(
        json=page(
            [
                sheet_json(),
                sheet_json(OTHER_ID, "Plan 2025"),
                sheet_json(CATALOG_ID, "Source Designers"),
                sheet_json(NO_COLUMN_ID, "Pagos"),
            ]
        )
    )
    data = {
        SHEET_ID: (columns("Designer1"), rows("Ana", "PEPE", None, "pepe")),
        OTHER_ID: (columns("Designer1"), rows("Luis", "Pepe", "Zoe")),
        CATALOG_ID: (columns("Designer"), rows("ana", " Luis ")),
        NO_COLUMN_ID: (columns("Monto"), []),
    }
    for sheet_id, (cols, sheet_rows) in data.items():
        smartsheet.get(f"/sheets/{sheet_id}/columns").respond(json=cols)

        def respond(
            request: httpx.Request, sheet_rows=sheet_rows, sheet_id=sheet_id
        ) -> httpx.Response:
            body = sheet_json(sheet_id) | {"totalRowCount": len(sheet_rows), "rows": sheet_rows}
            return httpx.Response(200, json=body)

        smartsheet.get(f"/sheets/{sheet_id}").mock(side_effect=respond)


PARAMS = {
    "column": "Designer1",
    "catalog_sheet": f"Pk{CATALOG_ID}Code",
    "catalog_column": "designer",
}


async def test_sheet_references(client, smartsheet) -> None:
    mock(smartsheet)
    body = (await client.get(f"/api/sheets/{SHEET_ID}/references", params=PARAMS)).json()
    assert body["catalog_sheet"]["name"] == "Source Designers"
    assert (body["catalog_values_count"], body["checked_rows"], body["missing_count"]) == (2, 3, 2)
    assert [(m["value"], len(m["rows"])) for m in body["missing"]] == [("PEPE", 2)]
    assert writes(smartsheet) == []


async def test_account_references(client, smartsheet) -> None:
    mock(smartsheet)
    body = (await client.get("/api/references", params=PARAMS)).json()
    assert (body["sheets_checked"], body["sheets_without_column"]) == (2, 1)
    assert body["missing_total"] == 4
    assert [(v["value"].casefold(), v["sheets"], v["rows"]) for v in body["by_value"]] == [
        ("pepe", 2, 3),
        ("zoe", 1, 1),
    ]
    assert CATALOG_ID not in {row["sheet_id"] for row in body["sheets"]}
    assert writes(smartsheet) == []
