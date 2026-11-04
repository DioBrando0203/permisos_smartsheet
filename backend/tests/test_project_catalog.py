"""Catálogo de proyectos por HTTP y sincronización de la hoja catálogo, con Smartsheet simulado."""

import json
import re
from unittest.mock import AsyncMock

import httpx
import pytest
import respx
from pydantic import SecretStr

from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.project_catalog import CATALOG_COLUMNS, PROJECTS_SHEET, SOURCE_COLUMNS
from tests.conftest import BASE

TOKEN = "clave-sintetica-de-prueba"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
CATALOG = "999"
WRITES = {
    "app_read_only": False,
    "ids_writes_enabled": True,
    "ids_transition_approved": True,
    "ids_admin_token": SecretStr(TOKEN),
    "app_project_catalog_sheet": CATALOG,
}
CUSTOMERS = ["BS-Blue Stream", "CC-Crown Castle", "OT-Others"]


class FakeSheets:
    """Proyectos y una hoja catálogo; registra cada escritura recibida."""

    def __init__(self) -> None:
        self.workspace = {PROJECTS_SHEET: PILOT_WORKSPACE, CATALOG: PILOT_WORKSPACE}
        self.columns = {PROJECTS_SHEET: SOURCE_COLUMNS, CATALOG: CATALOG_COLUMNS}
        self.rows = {
            PROJECTS_SHEET: [
                ("KMV-BS-27-001", "BS-Blue Stream", "BS", ""),
                ("KMV-BS-27-002", "BS-Blue Stream", "BS", "KMV-BS-27-001"),
                ("KMV-CC-27-001", "CC-Crown Castle", "CC", "KMV-CC-26-563"),
                ("KMV-CC-27-002", "CC-Crown Castle", "CC", "KMV-BS-27-001"),
                ("KMV-OT-27-001", "OT-Others", "OT", "dato libre"),
            ],
            CATALOG: [],
        }
        self.writes: list[tuple[str, str, list]] = []

    def column_id(self, sheet: str, index: int) -> int:
        return (1000 if sheet == CATALOG else 100) + index

    def handle(self, request: httpx.Request) -> httpx.Response:
        sheet, rest = re.fullmatch(r"/2\.0/sheets/(\d+)(.*)", request.url.path).groups()
        if request.method != "GET":
            self.writes.append((request.method, sheet, json.loads(request.content)))
            return httpx.Response(200, json={"message": "SUCCESS", "resultCode": 0})
        if rest == "/columns":
            data = [
                {"id": self.column_id(sheet, i), "title": title, "index": i, "type": "PICKLIST"}
                | ({"options": CUSTOMERS} if title == "Customer" else {})
                | ({"options": ["KMV-CC-26-563"]} if title == "Linked Tracking" else {})
                for i, title in enumerate(self.columns[sheet])
            ]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        return httpx.Response(
            200,
            json={
                "id": int(sheet),
                "name": f"Hoja {sheet}",
                "accessLevel": "ADMIN",
                "workspace": {"id": int(self.workspace[sheet])},
                "rows": [self._row(sheet, n, values) for n, values in enumerate(self.rows[sheet])],
                "totalRowCount": len(self.rows[sheet]),
            },
        )

    def _row(self, sheet: str, number: int, values: tuple) -> dict:
        if sheet == PROJECTS_SHEET:
            stable, customer, code, linked = values
            values = (stable, stable, customer, code, stable.split("-")[0], linked)
        cells = [
            {"columnId": self.column_id(sheet, i), "value": value or None}
            for i, value in enumerate(values)
        ]
        return {"id": number + 1, "rowNumber": number + 1, "cells": cells}


@pytest.fixture
def fake():
    sheets = FakeSheets()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=sheets.handle)
        yield sheets


async def test_catalog_filters_bs_cc_ot_with_historical(make_client, fake) -> None:
    client = make_client()
    bs = (await client.get("/api/catalogs/projects?customer_code=BS")).json()
    assert [p["tracking_project"] for p in bs["projects"]] == ["KMV-BS-27-001", "KMV-BS-27-002"]
    cc = (await client.get("/api/catalogs/projects?customer_code=cc")).json()["projects"]
    assert [(p["tracking_project"], p["origin"]) for p in cc] == [
        ("KMV-CC-26-563", "historical"),
        ("KMV-CC-27-001", "current"),
        ("KMV-CC-27-002", "current"),
    ]
    current = await client.get("/api/catalogs/projects?customer_code=CC&include_historical=false")
    assert len(current.json()["projects"]) == 2
    ot = (await client.get("/api/catalogs/projects?customer_code=OT&company=KMV")).json()
    assert [p["customer"] for p in ot["projects"]] == ["OT-Others"]
    assert fake.writes == []


async def test_linked_tracking_validation(make_client, fake) -> None:
    client = make_client()
    report = (await client.get("/api/catalogs/linked-tracking")).json()
    assert report["counts"] == {
        "empty": 1,
        "current_valid": 1,
        "historical_valid": 1,
        "other_customer": 1,
        "invalid": 1,
    }
    issues = (await client.get("/api/catalogs/linked-tracking?only_issues=true")).json()
    assert [item["linked_tracking"] for item in issues["items"]] == ["KMV-BS-27-001", "dato libre"]
    assert fake.writes == []


async def test_sync_plan_and_sync_are_blocked_without_barriers(make_client, fake) -> None:
    plan = (await make_client().get("/api/catalogs/projects/sync-plan")).json()
    assert plan["dry_run"] is True and {c["action"] for c in plan["changes"]} == {"add"}
    client = make_client(ids_admin_token=SecretStr(TOKEN), app_project_catalog_sheet=CATALOG)
    assert (await client.post("/api/catalogs/projects/sync")).status_code == 401
    blocked = await client.post("/api/catalogs/projects/sync", headers=HEADERS)
    assert blocked.status_code == 403
    assert blocked.json()["detail"]["code"] == "CATALOG_SYNC_BLOCKED"
    for sheet in ("", PROJECTS_SHEET):
        response = await make_client(**WRITES | {"app_project_catalog_sheet": sheet}).post(
            "/api/catalogs/projects/sync", headers=HEADERS
        )
        assert response.status_code == 403
    fake.workspace[CATALOG] = "1234567890"
    outside = await make_client(**WRITES).post("/api/catalogs/projects/sync", headers=HEADERS)
    assert "Pruebas" in outside.json()["detail"]["message"]
    assert fake.writes == []


async def test_sync_adds_updates_and_never_deletes(make_client, fake) -> None:
    fake.rows[CATALOG] = [
        ("KMV-BS-27-001", "BS", "BS-Blue Stream", "KMV", "Actual"),
        ("KMV-CC-27-001", "BS", "BS-Blue Stream", "KMV", "Actual"),
        ("KMV-BS-20-100", "BS", "BS-Blue Stream", "KMV", "Histórico"),
    ]
    response = await make_client(**WRITES).post("/api/catalogs/projects/sync", headers=HEADERS)
    assert response.json()["counts"] == {"add": 4, "update": 1, "unchanged": 2, "conflict": 0}
    methods = {(method, sheet) for method, sheet, _ in fake.writes}
    # Sólo la hoja catálogo; nunca DELETE ni escrituras en Proyectos (Stable IDs intactos).
    assert methods == {("POST", CATALOG), ("PUT", CATALOG)}
    sort = next(body for method, _, body in fake.writes if "sortCriteria" in body)
    assert [item["columnId"] for item in sort["sortCriteria"]] == [1001, 1003, 1000]
    added = next(body for method, _, body in fake.writes if method == "POST")
    values = sorted(row["cells"][0]["value"] for row in added)
    assert values == ["KMV-BS-27-002", "KMV-CC-26-563", "KMV-CC-27-002", "KMV-OT-27-001"]
    historical = next(row for row in added if row["cells"][0]["value"] == "KMV-CC-26-563")
    assert historical["cells"][4]["value"] == "Histórico"
    updated = next(body for method, _, body in fake.writes if method == "PUT")
    assert updated == [
        {
            "id": 2,
            "cells": [
                {"columnId": 1001, "value": "CC"},
                {"columnId": 1002, "value": "CC-Crown Castle"},
            ],
        }
    ]


async def test_processor_runs_catalog_hook_and_isolates_failures(monkeypatch) -> None:
    import app.services.ids.monitor as module

    report = {"counts": {"already_stable": 1}, "pending_or_conflicting_rows": []}
    monkeypatch.setattr(module, "build_dry_run_report", AsyncMock(return_value=report))
    hook = AsyncMock(side_effect=RuntimeError("caído"))
    monitor = module.IdMonitor(AsyncMock(), True, 60, connector_factory=AsyncMock, after_cycle=hook)
    result = await monitor.run_cycle()
    # Un fallo del catálogo no interrumpe el ciclo de IDs.
    assert result["counts"] == {"already_stable": 1}
    assert monitor.last_catalog == {"error": "catalog_sync_failed"}
    hook.assert_awaited_once()
    simulation = module.IdMonitor(AsyncMock(), True, 60, after_cycle=hook)
    await simulation.run_cycle()
    assert hook.await_count == 1
