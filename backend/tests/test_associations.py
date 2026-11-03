from tests.conftest import writes
from tests.factories import SHEET_ID, page, sheet_json
from tests.test_references import CATALOG_ID, columns


def row(number: int, customer: str | None, project: str | None) -> dict:
    return {
        "id": 100 + number,
        "rowNumber": number,
        "cells": [
            {"columnId": 1, "value": "fila"},
            {"columnId": 10, "value": customer},
            {"columnId": 11, "value": project},
        ],
    }


async def test_project_associations(client, smartsheet) -> None:
    smartsheet.get("/sheets").respond(json=page([sheet_json(), sheet_json(CATALOG_ID, "Catálogo")]))
    data = {
        SHEET_ID: [
            row(1, " bs ", "PROY-1"),
            row(2, "CC", "proy-1"),
            row(3, None, "PROY-1"),
            row(4, "BS", "desconocido"),
            row(5, "BS", "ambiguo"),
            row(6, "BS", "sin-cliente"),
            row(7, "BS", None),
        ],
        CATALOG_ID: [
            row(1, "BS", "proy-1"),
            row(2, "bs", "PROY-1"),
            row(3, "BS", "ambiguo"),
            row(4, "CC", "ambiguo"),
            row(5, None, "sin-cliente"),
        ],
    }
    for sheet_id, sheet_rows in data.items():
        smartsheet.get(f"/sheets/{sheet_id}/columns").respond(json=columns("Cliente", "Proyecto"))
        smartsheet.get(f"/sheets/{sheet_id}").respond(
            json=sheet_json(sheet_id) | {"totalRowCount": len(sheet_rows), "rows": sheet_rows}
        )
    params = {
        "customer_column": "Cliente",
        "project_column": "Proyecto",
        "catalog_sheet": CATALOG_ID,
        "catalog_customer_column": "Cliente",
        "catalog_project_column": "Proyecto",
    }
    response = await client.get(f"/api/sheets/{SHEET_ID}/project-associations", params=params)
    assert response.status_code == 200
    body = response.json()
    assert body["checked_rows"] == 6
    assert body["issues_count"] == 5
    assert [issue["reason"] for issue in body["issues"]] == [
        "wrong_customer",
        "missing_customer",
        "unknown_project",
        "ambiguous_project",
        "ambiguous_project",
    ]
    assert writes(smartsheet) == []
    params["project_column"] = "Inexistente"
    response = await client.get(f"/api/sheets/{SHEET_ID}/project-associations", params=params)
    assert response.status_code == 404


async def test_report_limits_rows_without_losing_total(client, smartsheet) -> None:
    smartsheet.get("/sheets").respond(json=page([sheet_json(), sheet_json(CATALOG_ID, "Catálogo")]))
    for sheet_id, sheet_rows in (
        (SHEET_ID, [row(n, "BS", "no existe") for n in range(1, 202)]),
        (CATALOG_ID, []),
    ):
        smartsheet.get(f"/sheets/{sheet_id}/columns").respond(json=columns("Cliente", "Proyecto"))
        smartsheet.get(f"/sheets/{sheet_id}").respond(
            json=sheet_json(sheet_id) | {"totalRowCount": len(sheet_rows), "rows": sheet_rows}
        )
    response = await client.get(
        f"/api/sheets/{SHEET_ID}/project-associations",
        params={
            "customer_column": "Cliente",
            "project_column": "Proyecto",
            "catalog_sheet": CATALOG_ID,
            "catalog_customer_column": "Cliente",
            "catalog_project_column": "Proyecto",
        },
    )
    body = response.json()
    assert body["issues_count"] == 201
    assert len(body["issues"]) == 200
    assert body["truncated"] is True
    assert writes(smartsheet) == []
