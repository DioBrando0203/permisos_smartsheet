"""Presentable: madres con ID propio e hijas con el ID de su madre (SPEC-ID01 ID-37 a ID-39).

Smartsheet simulado con jerarquía y PostgreSQL temporal vacío, como tras reiniciar el registro.
"""

import json
import re

import httpx
import pytest
import respx

psycopg = pytest.importorskip("psycopg")

from app.services.ids.connector import Target  # noqa: E402
from app.services.ids.dry_run import PILOT_WORKSPACE  # noqa: E402
from app.services.ids.formats import EntityKind  # noqa: E402
from app.services.ids.monitor import IdMonitor  # noqa: E402
from app.services.ids.pilot import PRESENTABLE  # noqa: E402
from app.services.ids.preview import build_dry_run_report  # noqa: E402
from app.services.ids.runtime import assign_factory, build_connector, build_store  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import BASE, make_settings  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database
COLUMNS = (
    "Tracking Project",
    "Stable Tracking Project",
    "Customer",
    "Customer Code",
    "Date Received",
)
STABLE = 101
FLAGS = {
    "app_read_only": False,
    "ids_writes_enabled": True,
    "ids_transition_approved": True,
    "ids_processor_writes_enabled": True,
}


class Presentable:
    """Hoja con filas madre e hijas; la fórmula visible imita la real."""

    def __init__(self) -> None:
        self.rows: dict[int, dict] = {}
        self.version = 1
        self.puts: list[list] = []
        self.fail_puts = 0  # escrituras que se pierden sin respuesta (red caída)

    def add(self, row_id: int, *, parent: int | None = None, provisional: str = "", **cells):
        self.rows[row_id] = {"parent": parent, "provisional": provisional, "stable": "", **cells}

    def visible(self, row_id: int) -> str:
        row = self.rows[row_id]
        if row["stable"]:
            return row["stable"]
        return self.visible(row["parent"]) if row["parent"] else row["provisional"]

    def handle(self, request: httpx.Request) -> httpx.Response:
        rest = re.fullmatch(rf"/2\.0/sheets/{PRESENTABLE}(.*)", request.url.path).group(1)
        if request.method == "PUT":
            if self.fail_puts:
                self.fail_puts -= 1
                raise httpx.ReadTimeout("sin respuesta simulada", request=request)
            body = json.loads(request.content)
            for item in body:
                self.rows[int(item["id"])]["stable"] = item["cells"][0]["value"]
            self.puts.append(body)
            self.version += 1
            return httpx.Response(200, json={"message": "SUCCESS"})
        if rest == "/version":
            return httpx.Response(200, json={"version": self.version})
        if rest == "/columns":
            data = [{"id": 100 + i, "title": t, "index": i} for i, t in enumerate(COLUMNS)]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        if rest.startswith("/rows/"):
            return httpx.Response(200, json=self._row(int(rest.removeprefix("/rows/"))))
        rows = [self._row(row_id) for row_id in self.rows]
        return httpx.Response(
            200,
            json={
                "id": int(PRESENTABLE),
                "name": "Presentable",
                "accessLevel": "OWNER",
                "workspace": {"id": int(PILOT_WORKSPACE)},
                "rows": rows,
                "totalRowCount": len(rows),
            },
        )

    def _row(self, row_id: int) -> dict:
        row = self.rows[row_id]
        values = (self.visible(row_id), row["stable"], row.get("customer"), row.get("code"))
        cells = [{"columnId": 100 + i, "value": v or None} for i, v in enumerate(values)]
        cells.append({"columnId": 104, "value": row.get("received")})
        data = {"id": row_id, "rowNumber": row_id, "cells": cells}
        return data | ({"parentId": row["parent"]} if row["parent"] else {})


@pytest.fixture
def sheet():
    fake = Presentable()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
        yield fake


def _fresh(dsn: str) -> None:
    """Registro vacío pero inicializado: el estado tras reiniciar a 001."""
    with psycopg.connect(dsn) as conn:
        conn.execute("INSERT INTO estado_inicializacion_id DEFAULT VALUES")


def _project(fake: Presentable, row_id: int, provisional: str, code: str) -> None:
    customer = {"BS": "BS-Blue Stream", "CC": "CC-Crown Castle"}[code]
    fake.add(row_id, provisional=provisional, customer=customer, code=code, received="2026-10-12")


def _rows(dsn: str, sql: str) -> list:
    with psycopg.connect(dsn) as conn:
        return conn.execute(sql).fetchall()


async def test_mothers_get_ids_and_children_inherit(sheet, database) -> None:
    _fresh(database)
    _project(sheet, 1, "KMV-BS-26-001", "BS")
    sheet.add(2, parent=1, customer="BS-Blue Stream", code="BS")
    _project(sheet, 3, "KMV-CC-26-001", "CC")
    sheet.add(4, parent=3, customer="CC-Crown Castle", code="CC")
    _project(sheet, 5, "KMV-BS-26-002", "BS")
    settings = make_settings(**FLAGS)
    client = SmartsheetClient(settings)
    try:
        monitor = IdMonitor(
            client,
            True,
            60,
            connector_factory=assign_factory(settings, client, database),
            dsn=database,
        )
        first = await monitor.run_cycle()
        assert first["outcomes"] == {"confirmed": 3}
        assert first["counts"]["pending_parent"] == 2
        second = await monitor.run_cycle()
        assert second["outcomes"] == {"inherited": 2}
        third = await monitor.run_cycle()
        assert third["outcomes"] == {}
        assert third["counts"] == {"already_stable": 3, "child_inherited": 2}
    finally:
        await client.aclose()
    assert [sheet.rows[i]["stable"] for i in (1, 2, 3, 4, 5)] == [
        "KMV-BS-26-001",
        "KMV-BS-26-001",
        "KMV-CC-26-001",
        "KMV-CC-26-001",
        "KMV-BS-26-002",
    ]
    # Cada PUT toca sólo la celda Stable ID; las hijas no gastan número ni registro.
    assert all(len(body) == 1 and body[0]["cells"][0]["columnId"] == STABLE for body in sheet.puts)
    assert _rows(database, "SELECT count(*) FROM asignacion_id") == [(3,)]
    audit = _rows(database, "SELECT accion, count(*) FROM auditoria_id GROUP BY 1 ORDER BY 1")
    assert audit == [("confirmado", 3), ("reservado", 3)]


async def test_child_with_other_project_is_conflict(sheet, database) -> None:
    _fresh(database)
    _project(sheet, 1, "KMV-BS-26-001", "BS")
    sheet.add(2, parent=1, customer="BS-Blue Stream", code="BS")
    sheet.rows[2]["stable"] = "KMV-BS-26-077"
    settings = make_settings(**FLAGS)
    client = SmartsheetClient(settings)
    try:
        monitor = IdMonitor(
            client,
            True,
            60,
            connector_factory=assign_factory(settings, client, database),
            dsn=database,
        )
        await monitor.run_cycle()
        result = await monitor.run_cycle()
        # Una hija nunca recibe número propio, aunque se le pida directamente.
        connector = build_connector(settings, client, build_store(settings, database))
        direct = await connector.process(
            Target(int(PRESENTABLE), 2, EntityKind.PROJECT, "KMV-BS-26")
        )
    finally:
        await client.aclose()
    assert result["counts"] == {"already_stable": 1, "conflict": 1}
    assert direct.value == "denied"
    assert sheet.rows[2]["stable"] == "KMV-BS-26-077"
    assert len(sheet.puts) == 1


async def test_id_registered_for_another_row_is_reported(sheet, database) -> None:
    _fresh(database)
    with psycopg.connect(database) as conn:
        conn.execute("INSERT INTO secuencia_id VALUES ('project:KMV-BS-26', 460)")
        conn.execute(
            "INSERT INTO asignacion_id VALUES "
            "(%s, 9, 'project:KMV-BS-26', 460, 'KMV-BS-26-460', 'confirmado')",
            (int(PRESENTABLE),),
        )
    _project(sheet, 1, "KMV-BS-26-460", "BS")
    sheet.rows[1]["stable"] = "KMV-BS-26-460"
    _project(sheet, 2, "KMV-CC-26-718", "CC")
    sheet.rows[2]["stable"] = "KMV-CC-26-718"
    client = SmartsheetClient(make_settings(app_read_only=True))
    try:
        report = await build_dry_run_report(client, database)
    finally:
        await client.aclose()
    actions = {item["row_id"]: item["action"] for item in report["pending_or_conflicting_rows"]}
    assert actions == {"1": "conflict", "2": "register_existing"}
    assert sheet.puts == []


async def _cycle(settings, client, dsn: str) -> dict:
    factory = assign_factory(settings, client, dsn)
    return await IdMonitor(client, True, 60, connector_factory=factory, dsn=dsn).run_cycle()


async def test_copied_mother_gets_next_number(sheet, database) -> None:
    _fresh(database)
    _project(sheet, 1, "KMV-BS-26-001", "BS")
    settings = make_settings(**FLAGS)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        # Copia de la madre 1 (mismo cliente) y otra copia a la que se le cambió el cliente.
        _project(sheet, 2, "", "BS")
        sheet.rows[2]["stable"] = "KMV-BS-26-001"
        _project(sheet, 3, "", "CC")
        sheet.rows[3]["stable"] = "KMV-BS-26-001"
        report = await build_dry_run_report(client, database)
        plan = {
            i["row_id"]: (i["action"], i["proposed_id"])
            for i in report["pending_or_conflicting_rows"]
        }
        assert plan == {
            "2": ("renumber_copy", "KMV-BS-26-002"),
            "3": ("renumber_copy", "KMV-CC-26-001"),
        }
        result = await _cycle(settings, client, database)
        final = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert result["outcomes"] == {"confirmed": 2}
    assert final["counts"] == {"already_stable": 3}
    assert [sheet.rows[i]["stable"] for i in (1, 2, 3)] == [
        "KMV-BS-26-001",
        "KMV-BS-26-002",
        "KMV-CC-26-001",
    ]
    assert _rows(database, "SELECT count(*) FROM asignacion_id WHERE estado='confirmado'") == [(3,)]


async def test_copy_retries_with_same_reservation(sheet, database) -> None:
    _fresh(database)
    _project(sheet, 1, "KMV-BS-26-001", "BS")
    settings = make_settings(**FLAGS)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        _project(sheet, 2, "", "BS")
        sheet.rows[2]["stable"] = "KMV-BS-26-001"
        sheet.fail_puts = 1
        lost = await _cycle(settings, client, database)
        retry = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert lost["outcomes"] == {"pending": 1}
    assert retry["outcomes"] == {"confirmed": 1}
    assert sheet.rows[2]["stable"] == "KMV-BS-26-002"
    sequence = "SELECT ultimo_numero FROM secuencia_id WHERE ambito='project:KMV-BS-26'"
    assert _rows(database, sequence) == [(2,)]
