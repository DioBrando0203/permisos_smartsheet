"""Cambio de cliente y familia coherente en Presentable (SPEC-ID01 ID-44 a ID-47).

Smartsheet simulado con jerarquía, movimientos y comentarios; PostgreSQL temporal. Datos
sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re

import httpx
import pytest
import respx

psycopg = pytest.importorskip("psycopg")

from app.services.ids.formats import EntityKind  # noqa: E402
from app.services.ids.monitor import IdMonitor  # noqa: E402
from app.services.ids.pilot import PRESENTABLE  # noqa: E402
from app.services.ids.preview import build_dry_run_report  # noqa: E402
from app.services.ids.runtime import assign_factory, build_store  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import BASE, make_settings  # noqa: E402
from tests.test_id_presentable import COLUMNS, FLAGS, Presentable, _fresh, _rows  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database
FULL = (*COLUMNS, "Linked Tracking")
CELLS = {101: "stable", 102: "customer", 105: "linked"}
ON = FLAGS | {"ids_customer_change_enabled": True}
CUSTOMERS = {"BS": "BS-Blue Stream", "CC": "CC-Crown Castle"}


class Family(Presentable):
    """Presentable con Customer editable, Linked Tracking y movimientos; registra comentarios."""

    def __init__(self) -> None:
        super().__init__()
        self.comments: list[tuple[int, str]] = []
        self.moves: list[tuple[int, int]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        rest = re.fullmatch(rf"/2\.0/sheets/{PRESENTABLE}(.*)", request.url.path).group(1)
        if request.method == "POST" and rest.endswith("/discussions"):
            text = json.loads(request.content)["comment"]["text"]
            self.comments.append((int(rest.split("/")[2]), text))
            return httpx.Response(200, json={"result": {"comments": [{"id": 1}]}})
        if request.method == "PUT":
            return self._put(json.loads(request.content))
        if rest == "/columns":
            data = [{"id": 100 + i, "title": t, "index": i} for i, t in enumerate(FULL)]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        return super().handle(request)

    def _put(self, body: list) -> httpx.Response:
        for item in body:
            row = self.rows[int(item["id"])]
            if "siblingId" in item:
                row["parent"] = None
                self.moves.append((int(item["id"]), int(item["siblingId"])))
            for cell in item.get("cells", []):
                row[CELLS[cell["columnId"]]] = cell["value"]
                if cell["columnId"] == 102:
                    row["code"] = cell["value"].split("-")[0]
        self.puts.append(body)
        self.version += 1
        return httpx.Response(200, json={"message": "SUCCESS"})

    def _row(self, row_id: int) -> dict:
        data = super()._row(row_id)
        data["cells"].append({"columnId": 105, "value": self.rows[row_id].get("linked")})
        return data

    def project(self, row_id: int, code: str, *, parent: int | None = None, **extra) -> None:
        self.add(
            row_id,
            parent=parent,
            customer=CUSTOMERS[code],
            code=code,
            received="2026-10-12",
            **extra,
        )

    def switch(self, row_id: int, code: str) -> None:
        self.rows[row_id] |= {"customer": CUSTOMERS[code], "code": code}


@pytest.fixture
def sheet():
    fake = Family()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
        yield fake


async def _cycle(settings, client, dsn: str, change: bool = True) -> dict:
    factory = assign_factory(settings, client, dsn)
    monitor = IdMonitor(
        client, True, 60, connector_factory=factory, dsn=dsn, customer_change=change
    )
    return await monitor.run_cycle()


async def _plan(client, dsn: str) -> dict:
    report = await build_dry_run_report(client, dsn, customer_change=True)
    return {i["row_id"]: i["action"] for i in report["pending_or_conflicting_rows"]}


async def test_mother_customer_change_renumbers_and_family_follows(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001")
    sheet.project(2, "BS", parent=1)
    sheet.project(3, "CC", provisional="KMV-CC-26-001", linked="KMV-BS-26-001")
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        await _cycle(settings, client, database)
        sheet.switch(1, "CC")
        assert await _plan(client, database) == {"1": "rescope", "2": "pending_parent"}
        rescoped = await _cycle(settings, client, database)
        followed = await _cycle(settings, client, database)
        quiet = await _cycle(settings, client, database)
        sheet.switch(1, "BS")  # volver al cliente original también da un número nuevo
        back = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert rescoped["outcomes"] == {"rescoped": 1}
    assert followed["outcomes"] == {"followed": 1}
    assert quiet["counts"] == {"already_stable": 2, "child_inherited": 1}
    assert back["outcomes"] == {"rescoped": 1}
    assert sheet.rows[1]["stable"] == "KMV-BS-26-002"
    assert (sheet.rows[2]["customer"], sheet.rows[2]["stable"]) == (
        "CC-Crown Castle",
        "KMV-CC-26-002",
    )
    assert sheet.rows[3]["linked"] == "KMV-BS-26-002"
    # Nada técnico en la hoja: el rastro queda sólo en PostgreSQL.
    assert sheet.comments == []
    retired = "SELECT id_generado, motivo FROM id_retirado ORDER BY retirado"
    assert _rows(database, retired) == [
        ("KMV-BS-26-001", "customer"),
        ("KMV-CC-26-002", "customer"),
    ]


async def test_child_with_other_customer_moves_out_and_gets_own_id(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001")
    sheet.project(2, "BS", parent=1)
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        await _cycle(settings, client, database)
        sheet.switch(2, "CC")
        assert await _plan(client, database) == {"2": "detach_child"}
        detached = await _cycle(settings, client, database)
        numbered = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert detached["outcomes"] == {"detached": 1}
    assert numbered["outcomes"] == {"confirmed": 1}
    assert sheet.moves == [(2, 1)]
    assert sheet.rows[2]["parent"] is None
    assert sheet.rows[2]["stable"] == "KMV-CC-26-001"
    assert sheet.rows[1]["stable"] == "KMV-BS-26-001"
    assert sheet.comments == []


async def test_copied_child_takes_mother_id(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001")
    sheet.project(2, "BS", parent=1)
    sheet.rows[2]["stable"] = "KMV-BS-26-077"  # hija pegada desde otro proyecto
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        fixed = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert fixed["outcomes"] == {"inherited": 1}
    assert sheet.rows[2]["stable"] == "KMV-BS-26-001"


async def test_switch_off_keeps_ids_permanent(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001")
    settings = make_settings(**FLAGS)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database, change=False)
        sheet.switch(1, "CC")
        result = await _cycle(settings, client, database, change=False)
    finally:
        await client.aclose()
    assert result["counts"] == {"already_stable": 1}
    assert sheet.rows[1]["stable"] == "KMV-BS-26-001"
    assert sheet.comments == [] and sheet.moves == []


async def test_retired_id_is_never_registered_or_reused(database) -> None:
    _fresh(database)
    store = build_store(make_settings(**ON), database)
    sheet_id = int(PRESENTABLE)
    store.register_existing(sheet_id, 1, EntityKind.PROJECT, "KMV-BS-26-001")
    store.retire(sheet_id, 1, "KMV-BS-26-001", "customer")
    with pytest.raises(ValueError, match="retirado"):
        store.register_existing(sheet_id, 2, EntityKind.PROJECT, "KMV-BS-26-001")
    assert store.reserve(sheet_id, 1, EntityKind.PROJECT, "KMV-BS-26").value == "KMV-BS-26-002"
    audit = "SELECT accion FROM auditoria_id ORDER BY evento_id"
    assert _rows(database, audit) == [("inicializado",), ("retirado",), ("reservado",)]
