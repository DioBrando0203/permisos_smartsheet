"""Piloto de IDs simulado con estado: cuatro hojas, fórmula visible y PUT con fallos inyectables.

La columna visible imita la fórmula real: muestra el Stable ID si existe; si no, un valor
provisional. Sólo datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re

import httpx
import pytest
import respx

from app.services.ids.dry_run import PILOT_WORKSPACE
from tests.conftest import BASE

PROJECTS, TASKS, RECORDS, REVISIONS = (
    4365321059389316,
    73093952524164,
    8140679218941828,
    5463681132613508,
)
COLUMNS = {
    PROJECTS: (
        "Tracking Project",
        "Stable Tracking Project",
        "KMV/GALP",
        "Customer Code",
        "Date Received",
    ),
    TASKS: ("Task ID", "Stable Task ID", "Tracking Project", "Reference"),
    RECORDS: ("Request ID", "Stable Request ID", "Task ID"),
    REVISIONS: ("Revision ID", "Stable Revision ID", "Task ID"),
}
_BASE_COLUMN = {PROJECTS: 100, TASKS: 200, RECORDS: 300, REVISIONS: 400}


def column_id(sheet: int, title: str) -> int:
    return _BASE_COLUMN[sheet] + COLUMNS[sheet].index(title)


def stable_column(sheet: int) -> int:
    return column_id(sheet, COLUMNS[sheet][1])


class FakePilot:
    def __init__(self) -> None:
        self.rows: dict[int, dict[int, dict[str, str]]] = {sheet: {} for sheet in COLUMNS}
        self.versions = dict.fromkeys(COLUMNS, 1)
        self.workspace = dict.fromkeys(COLUMNS, PILOT_WORKSPACE)
        self.puts: list[tuple[int, list]] = []
        # "timeout": no se aplica y no hay respuesta; "error_applied": se aplica y responde 500.
        self.put_failures: list[str] = []

    def add(self, sheet: int, row_id: int, *, provisional: str = "", stable: str = "", **cells):
        """Celdas por título; `cells` usa nombres sin espacios: tracking, reference, task, ..."""
        titles = {
            "company": "KMV/GALP",
            "customer": "Customer Code",
            "received": "Date Received",
            "tracking": "Tracking Project",
            "reference": "Reference",
            "task": "Task ID",
        }
        row = {titles[key]: value for key, value in cells.items()}
        row["_provisional"] = provisional
        row[COLUMNS[sheet][1]] = stable
        self.rows[sheet][row_id] = row

    def stable(self, sheet: int, row_id: int) -> str:
        return self.rows[sheet][row_id][COLUMNS[sheet][1]]

    def handle(self, request: httpx.Request) -> httpx.Response:
        match = re.fullmatch(r"/2\.0/sheets/(\d+)(/.*)?", request.url.path)
        sheet = int(match.group(1)) if match else 0
        rest = (match.group(2) or "") if match else ""
        if sheet not in self.rows:
            return httpx.Response(404, json={"errorCode": 1006, "message": "Not Found"})
        if request.method == "PUT" and rest == "/rows":
            return self._put(sheet, json.loads(request.content), request)
        if rest == "/version":
            return httpx.Response(200, json={"version": self.versions[sheet]})
        if rest == "/columns":
            data = [
                {"id": column_id(sheet, title), "title": title, "index": index}
                for index, title in enumerate(COLUMNS[sheet])
            ]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        if rest.startswith("/rows/"):
            row_id = int(rest.removeprefix("/rows/"))
            if row_id not in self.rows[sheet]:
                return httpx.Response(404, json={"errorCode": 1006, "message": "Not Found"})
            return httpx.Response(200, json=self._row(sheet, row_id))
        rows = [self._row(sheet, row_id) for row_id in self.rows[sheet]]
        return httpx.Response(
            200,
            json={
                "id": sheet,
                "name": f"Hoja {sheet}",
                "accessLevel": "ADMIN",
                "workspace": {"id": int(self.workspace[sheet])},
                "rows": rows,
                "totalRowCount": len(rows),
            },
        )

    def _row(self, sheet: int, row_id: int) -> dict:
        row = self.rows[sheet][row_id]
        visible = row[COLUMNS[sheet][1]] or row["_provisional"]
        values = {COLUMNS[sheet][0]: visible} | {k: v for k, v in row.items() if k[0] != "_"}
        cells = [
            {"columnId": column_id(sheet, title), "value": value or None}
            for title, value in values.items()
        ]
        return {"id": row_id, "rowNumber": row_id, "cells": cells}

    def _put(self, sheet: int, body: list, request: httpx.Request) -> httpx.Response:
        failure = self.put_failures.pop(0) if self.put_failures else None
        if failure == "timeout":
            raise httpx.ReadTimeout("sin respuesta simulada", request=request)
        for item in body:
            row = self.rows[sheet][int(item["id"])]
            for cell in item["cells"]:
                index = int(cell["columnId"]) - _BASE_COLUMN[sheet]
                row[COLUMNS[sheet][index]] = cell["value"]
        self.puts.append((sheet, body))
        self.versions[sheet] += 1
        if failure == "error_applied":
            return httpx.Response(500, json={"errorCode": 4000, "message": "Error simulado"})
        return httpx.Response(200, json={"message": "SUCCESS", "resultCode": 0})


@pytest.fixture
def pilot():
    fake = FakePilot()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
        yield fake
