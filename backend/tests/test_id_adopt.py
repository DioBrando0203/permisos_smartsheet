"""Permiso creado fuera de la jerarquía pasa bajo su proyecto (SPEC-ID01 ID-51).

Smartsheet simulado con jerarquía y movimientos; PostgreSQL temporal. Datos sintéticos;
ninguna solicitud sale a Smartsheet.
"""

import httpx
import pytest
import respx

psycopg = pytest.importorskip("psycopg")

from app.services.ids import customer_change  # noqa: E402
from app.services.ids.connector import ChildSnapshot, Outcome, Target  # noqa: E402
from app.services.ids.dry_run import PILOT_WORKSPACE  # noqa: E402
from app.services.ids.formats import EntityKind  # noqa: E402
from app.services.ids.pilot import PRESENTABLE  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import BASE, make_settings  # noqa: E402
from tests.test_id_customer_change import FULL, ON, Family, _cycle, _plan  # noqa: E402
from tests.test_id_presentable import _fresh, _rows  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database
COLUMNS = (*FULL, "Type of Project")
TYPE = 100 + len(FULL)


class Hierarchy(Family):
    """Family con `Type of Project` y filas que se pueden indentar (`parentId`)."""

    def __init__(self) -> None:
        super().__init__()
        self.adopted: list[tuple[int, int]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/columns"):
            data = [{"id": 100 + i, "title": t, "index": i} for i, t in enumerate(COLUMNS)]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        return super().handle(request)

    def _put(self, body: list) -> httpx.Response:
        for item in body:
            if "parentId" in item:
                self.rows[int(item["id"])]["parent"] = int(item["parentId"])
                self.adopted.append((int(item["id"]), int(item["parentId"])))
        return super()._put(body)

    def _row(self, row_id: int) -> dict:
        data = super()._row(row_id)
        data["cells"].append({"columnId": TYPE, "value": self.rows[row_id].get("type")})
        return data


@pytest.fixture
def sheet():
    fake = Hierarchy()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
        yield fake


async def test_loose_permit_goes_under_its_project_without_spending_a_number(
    sheet, database
) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001", type="KMV-P")
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        sheet.project(2, "BS", type="KMV-Permit", linked="KMV-BS-26-001")
        planned = await _plan(client, database)
        adopted = await _cycle(settings, client, database)
        inherited = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert planned == {"2": "adopt_permit"}
    assert adopted["outcomes"] == {"adopted": 1}
    assert inherited["outcomes"] == {"inherited": 1}
    assert sheet.adopted == [(2, 1)]
    assert (sheet.rows[2]["parent"], sheet.rows[2]["stable"]) == (1, "KMV-BS-26-001")
    assert _rows(database, "SELECT fila_id FROM asignacion_id WHERE fila_id = 2") == []
    assert sheet.comments == []


async def test_permit_with_own_id_takes_the_project_id(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001", type="KMV-P")
    sheet.project(2, "BS", provisional="KMV-BS-26-002", type="KMV-Line")
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        await _cycle(settings, client, database)
        sheet.rows[2]["linked"] = "KMV-BS-26-001"
        adopted = await _cycle(settings, client, database)
        fixed = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert adopted["outcomes"] == {"adopted": 1}
    assert fixed["outcomes"] == {"inherited": 1}
    assert sheet.rows[2]["stable"] == "KMV-BS-26-001"


@pytest.mark.parametrize(
    ("kind", "code", "linked"),
    [
        ("KMV-P", "BS", "KMV-BS-26-001"),  # no es permiso
        ("KMV-Permit", "CC", "KMV-BS-26-001"),  # otro cliente
        ("KMV-Permit", "BS", "KMV-BS-26-099"),  # proyecto inexistente
        ("KMV-Permit", "BS", ""),  # sin Linked Tracking
    ],
)
async def test_rows_that_do_not_qualify_are_left_alone(
    sheet, database, kind: str, code: str, linked: str
) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001", type="KMV-P")
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        sheet.project(2, code, type=kind, linked=linked)
        planned = await _plan(client, database)
    finally:
        await client.aclose()
    assert planned.get("2") != "adopt_permit"
    assert sheet.adopted == []


async def test_switch_off_does_not_adopt(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="KMV-BS-26-001", type="KMV-P")
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database, change=False)
        sheet.project(2, "BS", type="KMV-Permit", linked="KMV-BS-26-001")
        await _cycle(settings, client, database, change=False)
    finally:
        await client.aclose()
    assert sheet.adopted == []


class _Lock:
    def execute(self, _sql: str) -> None:
        return None

    def close(self) -> None:
        return None


class _Store:
    def lock_sheet(self, _sheet_id: int) -> _Lock:
        return _Lock()


class _Gateway:
    """Fila que cambió entre el plan y la escritura: otro Linked Tracking."""

    def __init__(self, linked: str) -> None:
        self.linked = linked
        self.moved = False

    async def read_child(self, _target: Target) -> ChildSnapshot:
        return ChildSnapshot(PILOT_WORKSPACE, None, "", "")

    async def permit_link(self, _target: Target) -> tuple[str, str]:
        return "KMV-Permit", self.linked

    async def read_stable(self, _target: Target, _row: int) -> str:
        return "KMV-BS-26-001"

    async def customer_codes(self, _target: Target, _row: int) -> tuple[str, str]:
        return "BS", "BS"

    async def move_under(self, _target: Target, _row: int) -> None:
        self.moved = True


@pytest.mark.parametrize(("linked", "outcome"), [("KMV-BS-26-007", "pending"), ("", "pending")])
async def test_adoption_rechecks_the_row_before_moving(linked: str, outcome: str) -> None:
    gateway = _Gateway(linked)
    target = Target(int(PRESENTABLE), 2, EntityKind.PROJECT, "KMV-BS-26-001")
    result = await customer_change.run("adopt_permit", _Store(), gateway, target, 1)
    assert result == Outcome(outcome) and not gateway.moved
    assert (
        await customer_change.run("adopt_permit", _Store(), _Gateway("KMV-BS-26-001"), target, 1)
    ) == Outcome.ADOPTED
