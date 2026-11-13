"""Hoja hija de Records (SPEC-B18 CA-01 a CA-04): reglas puras y paso con Smartsheet simulado.

Datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.monitor import IdMonitor
from app.services.records import rules
from app.services.records.sync import RecordsSync, records_hook
from app.services.smartsheet import SmartsheetClient
from tests.conftest import BASE, make_settings

CHILD = "777"
WRITES = {
    "app_read_only": False,
    "ids_writes_enabled": True,
    "ids_transition_approved": True,
    "app_records_sync_enabled": True,
    "app_records_sheet_id": CHILD,
}
TYPES = {"Date Received": "DATE", "Record Request": "DATE", "Records Needed": "CHECKBOX"}
MASTER_TITLES = [*rules.CONTEXT, "Records Needed", "Designer2", "PRR #", "Record Request"]
CHILD_TITLES = [*rules.CONTEXT, "Master Row", "Designer2", "PRR #", "Record Request"]


def master(row_id: str, needed: bool, tracking: str, **values) -> rules.MasterRow:
    return rules.MasterRow(row_id, needed, {"Tracking Project": tracking, **values})


def test_plan_creates_waits_and_skips() -> None:
    masters = [
        master("1", True, "KMV-BS-26-001", **{"Project Name": "A"}),
        master("2", True, "Pending ID"),
        master("3", False, "KMV-CC-26-002"),
    ]
    result = rules.plan(masters, [])
    assert [row.row_id for row in result.create] == ["1"]
    assert result.waiting == 1 and result.update == []


def test_plan_updates_changed_context_even_unchecked_and_never_duplicates() -> None:
    masters = [master("1", False, "KMV-CC-26-005", **{"Project Name": "A"})]
    children = [
        rules.ChildRow("90", "1", {"Tracking Project": "KMV-BS-26-001", "Project Name": "A"}),
        rules.ChildRow("91", "1", {"Tracking Project": "otra"}),
    ]
    result = rules.plan(masters, children)
    assert result.create == []
    assert result.update == [("90", {"Tracking Project": "KMV-CC-26-005"})]
    assert (
        rules.plan(
            [master("1", True, "KMV-BS-26-001", City="")],
            [rules.ChildRow("90", "1", {"Tracking Project": "KMV-BS-26-001"})],
        ).update
        == []
    )


class TwoSheets:
    """Maestra y hoja hija; registra POST y PUT de filas."""

    def __init__(self) -> None:
        self.workspace = {pilot.PRESENTABLE: PILOT_WORKSPACE, CHILD: PILOT_WORKSPACE}
        self.master: dict[str, dict] = {}
        self.child: dict[str, dict] = {}
        self.posts: list[list] = []
        self.puts: list[list] = []
        self.next_id = 500

    def columns(self, sheet: str) -> list[str]:
        return MASTER_TITLES if sheet == pilot.PRESENTABLE else CHILD_TITLES

    def handle(self, request: httpx.Request) -> httpx.Response:
        match = re.fullmatch(r"/2\.0/sheets/(\d+)(/.*)?", request.url.path)
        sheet, rest = match.group(1), match.group(2) or ""
        titles = self.columns(sheet)
        if rest == "/columns":
            data = [
                {"id": i + 1, "title": t, "index": i, "type": TYPES.get(t, "TEXT_NUMBER")}
                for i, t in enumerate(titles)
            ]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        if rest == "/rows" and request.method in ("POST", "PUT"):
            body = json.loads(request.content)
            (self.posts if request.method == "POST" else self.puts).append(body)
            for item in body:
                values = {titles[c["columnId"] - 1]: c["value"] for c in item["cells"]}
                if request.method == "POST":
                    self.next_id += 1
                    self.child[str(self.next_id)] = values
                else:
                    self.child[str(item["id"])].update(values)
            return httpx.Response(200, json={"message": "SUCCESS", "result": []})
        rows_source = self.master if sheet == pilot.PRESENTABLE else self.child
        rows = [
            {
                "id": int(row_id),
                "cells": [
                    {"columnId": titles.index(t) + 1, "value": v}
                    for t, v in values.items()
                    if t in titles
                ],
            }
            for row_id, values in rows_source.items()
        ]
        body = {"id": int(sheet), "workspace": {"id": int(self.workspace[sheet])}}
        return httpx.Response(200, json=body | {"rows": rows, "totalRowCount": len(rows)})


@pytest.fixture
def sheets():
    fake = TwoSheets()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
        yield fake


def _sync(**overrides) -> tuple[RecordsSync, SmartsheetClient]:
    settings = make_settings(**(WRITES | overrides))
    client = SmartsheetClient(settings)
    return RecordsSync(settings, client, interval=0), client


async def test_creates_once_copies_context_and_initial_values(sheets) -> None:
    sheets.master = {
        "1": {
            "Tracking Project": "KMV-BS-26-001",
            "Project Name": "Palm Tower",
            "Date Received": "2026-10-12",
            "Records Needed": True,
            "Designer2": "Persona Uno",
            "PRR #": "PRR-7",
            "Record Request": "2026-11-01",
        },
        "2": {"Tracking Project": "Pending ID", "Records Needed": True},
        "3": {"Tracking Project": "KMV-CC-26-002", "Records Needed": False},
    }
    sync, client = _sync()
    try:
        first = await sync.run()
        second = await sync.run()
    finally:
        await client.aclose()
    assert first == {"created": 1, "updated": 0, "waiting": 1, "deferred": 0}
    assert second["created"] == 0 and second["updated"] == 0
    (created,) = sheets.child.values()
    assert created == {
        "Master Row": "1",
        "Tracking Project": "KMV-BS-26-001",
        "Project Name": "Palm Tower",
        "Date Received": "2026-10-12",
        "Designer2": "Persona Uno",
        "PRR #": "PRR-7",
        "Record Request": "2026-11-01",
    }
    assert sheets.posts[0][0]["toBottom"] is True and len(sheets.posts) == 1


async def test_context_follows_master_and_unchecking_never_deletes(sheets) -> None:
    sheets.master = {
        "1": {"Tracking Project": "KMV-BS-26-001", "City": "Doral", "Records Needed": True}
    }
    sync, client = _sync()
    try:
        await sync.run()
        sheets.master["1"].update(
            {"Tracking Project": "KMV-CC-26-005", "City": "", "Records Needed": False}
        )
        changed = await sync.run()
    finally:
        await client.aclose()
    assert changed["updated"] == 1 and changed["created"] == 0
    (row,) = sheets.child.values()
    assert row["Tracking Project"] == "KMV-CC-26-005" and row["City"] == ""
    assert len(sheets.child) == 1


async def test_barriers_and_hook(sheets) -> None:
    sheets.master = {"1": {"Tracking Project": "KMV-BS-26-001", "Records Needed": True}}
    sheets.workspace[CHILD] = "123"
    sync, client = _sync()
    try:
        with pytest.raises(ValueError, match="Pruebas"):
            await sync.run()
        sheets.workspace[CHILD] = PILOT_WORKSPACE
        sheets.columns = lambda sheet: [t for t in MASTER_TITLES if t != "Records Needed"]
        with pytest.raises(ValueError, match="Columnas"):
            await _sync()[0].run()
    finally:
        await client.aclose()
    assert sheets.posts == [] and sheets.puts == []
    assert (
        records_hook(make_settings(**WRITES | {"app_records_sync_enabled": False}), client) is None
    )
    assert records_hook(make_settings(**WRITES | {"app_records_sheet_id": ""}), client) is None
    assert records_hook(make_settings(**WRITES | {"app_read_only": True}), client) is None
    assert records_hook(make_settings(**WRITES), client) is not None


async def test_monitor_isolates_records_failures(monkeypatch) -> None:
    import app.services.ids.monitor as module

    report = {"counts": {}, "pending_or_conflicting_rows": []}
    monkeypatch.setattr(module, "build_dry_run_report", AsyncMock(return_value=report))
    step = AsyncMock(side_effect=RuntimeError("falla"))
    monitor = IdMonitor(AsyncMock(), True, 60, connector_factory=AsyncMock, records_sync=step)
    result = await monitor.run_cycle()
    assert result["counts"] == {}
    assert monitor.last_records == {"error": "records_failed", "type": "RuntimeError"}
