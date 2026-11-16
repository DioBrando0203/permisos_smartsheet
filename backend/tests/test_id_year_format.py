"""IDs de proyecto por año, sin cliente (SPEC-ID01 ID-52, ID-53; maestra 2.0, PEN-54).

Funciones puras y un ciclo completo con Smartsheet simulado y PostgreSQL temporal.
Datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

from datetime import date

import pytest

from app.services.ids import pilot
from app.services.ids.formats import (
    EntityKind,
    customer_code,
    make_id,
    parse_id,
    project_scope,
)

P = EntityKind.PROJECT


def test_year_ids_have_four_digits_and_customer_ids_keep_three() -> None:
    assert make_id(P, "KMV-26", 1) == "KMV-26-0001"
    assert make_id(P, "KMV-26", 12345) == "KMV-26-12345"
    assert make_id(P, "KMV-CC-26", 1) == "KMV-CC-26-001"
    assert parse_id(P, "KMV-26-0001").parent == "KMV-26"
    assert parse_id(P, "KMV-CC-26-001").parent == "KMV-CC-26"
    for wrong in ("KMV-26-001", "KMV-26-00001", "KMV-CC-26-0001"):
        with pytest.raises(ValueError):
            parse_id(P, wrong)
    assert make_id(EntityKind.TASK, "KMV-26-0001", 2) == "KMV-26-0001-02"


def test_year_scope_still_needs_a_customer() -> None:
    received = date(2026, 10, 12)
    assert project_scope("KMV", "CC", received, with_customer=False) == "KMV-26"
    assert project_scope("KMV", "CC", received) == "KMV-CC-26"
    assert project_scope("KMV", "", received, with_customer=False) == ""
    assert customer_code("KMV-26") == "" and customer_code("KMV-CC-26") == "CC"


psycopg = pytest.importorskip("psycopg")

from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import make_settings  # noqa: E402
from tests.test_id_adopt import Hierarchy  # noqa: E402
from tests.test_id_customer_change import ON, _cycle, _plan  # noqa: E402
from tests.test_id_presentable import _fresh  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database


@pytest.fixture
def sheet(monkeypatch):
    import respx

    from tests.conftest import BASE

    monkeypatch.setattr(pilot, "YEAR_FORMAT", True)
    fake = Hierarchy()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
        yield fake


async def test_one_counter_per_year_for_every_customer(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="Pending ID", type="KMV-P")
    sheet.project(2, "CC", provisional="Pending ID", type="KMV-Miscellaneous")
    sheet.project(3, "CC", parent=1, type="KMV-Line")  # otro cliente que su madre: la sigue
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert {sheet.rows[1]["stable"], sheet.rows[2]["stable"]} == {"KMV-26-0001", "KMV-26-0002"}
    assert sheet.rows[3]["stable"] == sheet.rows[1]["stable"]
    assert sheet.rows[3]["parent"] == 1  # sin cliente en el ID, nunca sale de la familia


async def test_loose_permit_waits_for_its_project_and_then_moves_under_it(sheet, database) -> None:
    _fresh(database)
    sheet.project(1, "BS", provisional="Pending ID", type="KMV-P")
    sheet.project(2, "BS", provisional="Pending ID", type="KMV-Permit")
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        await _cycle(settings, client, database)
        waiting = await _plan(client, database)
        sheet.rows[2]["project"] = sheet.rows[1]["stable"]
        planned = await _plan(client, database)
        adopted = await _cycle(settings, client, database)
        inherited = await _cycle(settings, client, database)
    finally:
        await client.aclose()
    assert sheet.rows[1]["stable"] == "KMV-26-0001"
    assert "2" not in waiting  # sin número ni acción mientras no elija su proyecto
    assert planned["2"] == "adopt_permit"
    assert adopted["outcomes"] == {"adopted": 1} and inherited["outcomes"] == {"inherited": 1}
    assert (sheet.rows[2]["parent"], sheet.rows[2]["stable"]) == (1, "KMV-26-0001")
