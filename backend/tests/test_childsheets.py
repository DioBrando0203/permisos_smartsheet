"""Hojas hijas Records y Facturación (SPEC-B18, SPEC-B19): reglas y paso con Smartsheet simulado.

Datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re
from dataclasses import replace
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.services.childsheets import rules
from app.services.childsheets.specs import BILLING, RECORDS
from app.services.childsheets.sync import ChildSheetSync, child_hooks
from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.monitor import IdMonitor
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
DATES = {"Date Received", "Record Request", "PM Approval Date", "Invoice Sent"}
CHECKS = {"Records Needed", "Invoice? GALP"}


def master(row_id: str, needed: bool, tracking: str, **values) -> rules.MasterRow:
    return rules.MasterRow(row_id, needed, {"Tracking Project": tracking, **values})


def test_plan_creates_waits_skips_and_never_duplicates() -> None:
    masters = [
        master("1", True, "KMV-BS-26-001", **{"Project Name": "A"}),
        master("2", True, "Pending ID"),
        master("3", False, "KMV-CC-26-002"),
    ]
    result = rules.plan(RECORDS, masters, [])
    assert [row.row_id for row in result.create] == ["1"] and result.waiting == 1
    children = [
        rules.ChildRow("90", "3", {"Tracking Project": "KMV-BS-26-001"}),
        rules.ChildRow("91", "3", {"Tracking Project": "otra"}),
    ]
    again = rules.plan(RECORDS, [master("3", False, "KMV-CC-26-005", City="")], children)
    assert again.create == [] and again.update == [("90", {"Tracking Project": "KMV-CC-26-005"})]


def test_plan_summary_goes_back_and_derived_is_mirrored() -> None:
    spec = replace(BILLING, context=("Tracking Project",))
    masters = [master("1", True, "KMV-BS-26-001", **{"Invoice Status": None, "Row Type": "Permit"})]
    children = [
        rules.ChildRow(
            "90",
            "1",
            {"Tracking Project": "KMV-BS-26-001", "Invoice Status": "PAID", "Row Type": None},
        )
    ]
    result = rules.plan(spec, masters, children)
    assert result.update == [("90", {"Row Type": "Permit"})]
    assert result.summary == [("1", {"Invoice Status": "PAID"})]


class TwoSheets:
    """Maestra y hoja hija con columnas configurables; registra POST y PUT de filas."""

    def __init__(self, master_titles: list[str], child_titles: list[str]) -> None:
        self.titles = {pilot.PRESENTABLE: master_titles, CHILD: child_titles}
        self.formulas: set[str] = set()
        self.workspace = {pilot.PRESENTABLE: PILOT_WORKSPACE, CHILD: PILOT_WORKSPACE}
        self.rows: dict[str, dict[str, dict]] = {pilot.PRESENTABLE: {}, CHILD: {}}
        self.parents: dict[str, str] = {}
        self.writes: list[tuple[str, str, list]] = []
        self.next_id = 500

    def handle(self, request: httpx.Request) -> httpx.Response:
        match = re.fullmatch(r"/2\.0/sheets/(\d+)(/.*)?", request.url.path)
        sheet, rest = match.group(1), match.group(2) or ""
        titles = self.titles[sheet]
        if rest == "/columns":
            data = [
                {"id": i + 1, "title": t, "index": i, "type": _type(t)}
                | ({"formula": "=x"} if sheet == pilot.PRESENTABLE and t in self.formulas else {})
                for i, t in enumerate(titles)
            ]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        if rest == "/rows" and request.method in ("POST", "PUT"):
            body = json.loads(request.content)
            self.writes.append((sheet, request.method, body))
            for item in body:
                values = {titles[c["columnId"] - 1]: c["value"] for c in item["cells"]}
                if request.method == "POST":
                    self.next_id += 1
                    self.rows[sheet][str(self.next_id)] = values
                else:
                    self.rows[sheet][str(item["id"])].update(values)
            return httpx.Response(200, json={"message": "SUCCESS", "result": []})
        rows = [
            {
                "id": int(row_id),
                "cells": [
                    {"columnId": titles.index(t) + 1, "value": v}
                    for t, v in values.items()
                    if t in titles
                ],
            }
            | ({"parentId": int(self.parents[row_id])} if row_id in self.parents else {})
            for row_id, values in self.rows[sheet].items()
        ]
        body = {"id": int(sheet), "workspace": {"id": int(self.workspace[sheet])}}
        return httpx.Response(200, json=body | {"rows": rows, "totalRowCount": len(rows)})


def _type(title: str) -> str:
    return "DATE" if title in DATES else "CHECKBOX" if title in CHECKS else "TEXT_NUMBER"


@pytest.fixture
def router():
    with respx.mock(assert_all_called=False) as mock:
        yield mock


def _sheets(router, master_titles: list[str], child_titles: list[str]) -> TwoSheets:
    fake = TwoSheets(master_titles, child_titles)
    router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
    return fake


RECORDS_MASTER = [*RECORDS.context, "Records Needed", "PRR #", "Record Request"]
RECORDS_CHILD = [*RECORDS.context, "Master Row", "PRR #", "Record Request"]


async def test_records_creates_once_and_follows_context(router) -> None:
    sheets = _sheets(router, RECORDS_MASTER, RECORDS_CHILD)
    sheets.rows[pilot.PRESENTABLE] = {
        "1": {
            "Tracking Project": "KMV-BS-26-001",
            "City": "Doral",
            "Date Received": "2026-10-12",
            "Records Needed": True,
            "PRR #": "PRR-7",
            "Record Request": "2026-11-01",
        },
        "2": {"Tracking Project": "Pending ID", "Records Needed": True},
        "3": {"Tracking Project": "KMV-CC-26-002", "Records Needed": False},
    }
    settings = make_settings(**WRITES)
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, RECORDS, CHILD, interval=0)
    try:
        first = await sync.run()
        second = await sync.run()
        sheets.rows[pilot.PRESENTABLE]["1"].update({"City": "", "Records Needed": False})
        third = await sync.run()
    finally:
        await client.aclose()
    assert first == {"created": 1, "updated": 0, "summarized": 0, "waiting": 1, "deferred": 0}
    assert second["created"] == 0 and second["updated"] == 0
    assert third["updated"] == 1
    (row,) = sheets.rows[CHILD].values()
    assert row["Master Row"] == "1" and row["PRR #"] == "PRR-7"
    assert row["Record Request"] == "2026-11-01" and row["City"] == ""


BILLING_MASTER = [*BILLING.context, "Invoice? GALP", "Invoice Sent", "Invoice Status"]
BILLING_CHILD = [
    *BILLING.context,
    "Row Type",
    "Master Row",
    "Invoice? GALP",
    "Invoice Sent",
    "Invoice Status",
]


async def test_billing_mirrors_every_row_with_id_and_returns_status(router) -> None:
    sheets = _sheets(router, BILLING_MASTER, BILLING_CHILD)
    sheets.rows[pilot.PRESENTABLE] = {
        "1": {"Tracking Project": "KMV-BS-26-001", "Total Footage": "300", "Invoice? GALP": True},
        "2": {"Tracking Project": "KMV-BS-26-001", "Invoice Sent": "2026-11-02"},
        "3": {"Tracking Project": "Pending ID"},
    }
    sheets.parents["2"] = "1"
    sheets.formulas.add("Invoice Status")
    settings = make_settings(
        **WRITES | {"app_billing_sync_enabled": True, "app_billing_sheet_id": CHILD}
    )
    client = SmartsheetClient(settings)
    sync = ChildSheetSync(settings, client, BILLING, CHILD, interval=0)
    try:
        created = await sync.run()
        for row in sheets.rows[CHILD].values():
            row["Invoice Status"] = "PAID"
        blocked = await sync.run()
        sheets.formulas.clear()
        returned = await sync.run()
    finally:
        await client.aclose()
    assert created["created"] == 2 and created["waiting"] == 1
    kinds = sorted((r["Master Row"], r["Row Type"]) for r in sheets.rows[CHILD].values())
    assert kinds == [("1", "Project"), ("2", "Permit")]
    first = next(r for r in sheets.rows[CHILD].values() if r["Master Row"] == "1")
    assert first["Total Footage"] == "300" and first["Invoice? GALP"] is True
    # Con fórmula en la maestra el resumen no vuelve; sin fórmula, sí.
    assert blocked["summarized"] == 0
    assert returned["summarized"] == 2
    assert {
        r.get("Invoice Status")
        for r in sheets.rows[pilot.PRESENTABLE].values()
        if r["Tracking Project"] != "Pending ID"
    } == {"PAID"}


async def test_barriers_and_hooks(router) -> None:
    sheets = _sheets(router, RECORDS_MASTER, RECORDS_CHILD)
    sheets.workspace[CHILD] = "123"
    settings = make_settings(**WRITES)
    client = SmartsheetClient(settings)
    try:
        with pytest.raises(ValueError, match="Pruebas"):
            await ChildSheetSync(settings, client, RECORDS, CHILD, interval=0).run()
        sheets.workspace[CHILD] = PILOT_WORKSPACE
        sheets.titles[pilot.PRESENTABLE] = [t for t in RECORDS_MASTER if t != "Records Needed"]
        with pytest.raises(ValueError, match="Columnas"):
            await ChildSheetSync(settings, client, RECORDS, CHILD, interval=0).run()
    finally:
        await client.aclose()
    assert sheets.writes == []
    assert child_hooks(make_settings(**WRITES | {"app_records_sync_enabled": False}), client) == {}
    assert child_hooks(make_settings(**WRITES | {"app_read_only": True}), client) == {}
    both = WRITES | {"app_billing_sync_enabled": True, "app_billing_sheet_id": "888"}
    assert set(child_hooks(make_settings(**both), client)) == {"records", "billing"}


async def test_monitor_isolates_each_child_sheet(monkeypatch) -> None:
    import app.services.ids.monitor as module

    report = {"counts": {}, "pending_or_conflicting_rows": []}
    monkeypatch.setattr(module, "build_dry_run_report", AsyncMock(return_value=report))
    steps = {
        "records": AsyncMock(side_effect=RuntimeError("falla")),
        "billing": AsyncMock(return_value={"created": 1}),
    }
    monitor = IdMonitor(AsyncMock(), True, 60, connector_factory=AsyncMock, child_syncs=steps)
    result = await monitor.run_cycle()
    assert result["counts"] == {}
    assert monitor.last_children == {
        "records": {"error": "records_failed", "type": "RuntimeError"},
        "billing": {"created": 1},
    }
