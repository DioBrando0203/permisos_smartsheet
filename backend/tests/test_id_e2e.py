"""Cadena completa del ID Manager: cliente, adaptador, coordinador, DRY_RUN y procesador.

Smartsheet simulado con estado (`fake_pilot`) y PostgreSQL temporal; datos sintéticos.
"""

import pytest

psycopg = pytest.importorskip("psycopg")

from app.core.errors import AppError  # noqa: E402
from app.services.ids import database as id_database  # noqa: E402
from app.services.ids.formats import EntityKind  # noqa: E402
from app.services.ids.manual import assign_row  # noqa: E402
from app.services.ids.monitor import _LOCK, IdMonitor  # noqa: E402
from app.services.ids.preview import build_dry_run_report  # noqa: E402
from app.services.ids.recovery import plan_recovery  # noqa: E402
from app.services.ids.runtime import assign_factory  # noqa: E402
from app.services.ids.store import ExistingId, IdStore  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import make_settings  # noqa: E402
from tests.fake_pilot import PROJECTS, RECORDS, REVISIONS, TASKS, pilot, stable_column  # noqa: E402
from tests.test_ids import database  # noqa: E402

pilot = pilot
database = database
PROJECT = "KMV-BS-26-452"
TASK = f"{PROJECT}-01"
NEW_TASK = f"{PROJECT}-02"
WRITE_FLAGS = {
    "app_read_only": False,
    "ids_writes_enabled": True,
    "ids_transition_approved": True,
    "ids_processor_writes_enabled": True,
}


def _seed(fake, dsn: str) -> None:
    """Proyecto y tarea importados, como los 19 IDs reales del piloto."""
    fake.add(PROJECTS, 1, stable=PROJECT, company="KMV", customer="BS", received="2026-03-02")
    fake.add(TASKS, 10, stable=TASK, tracking=PROJECT, reference=PROJECT)
    IdStore(dsn).initialize(
        [
            ExistingId(PROJECTS, 1, EntityKind.PROJECT, PROJECT),
            ExistingId(TASKS, 10, EntityKind.TASK, TASK),
        ]
    )


def _new_task(fake, provisional: str = NEW_TASK, stable: str = "") -> None:
    fake.add(TASKS, 11, provisional=provisional, stable=stable, tracking=PROJECT, reference=PROJECT)


def _rows(dsn: str, sql: str) -> list:
    with psycopg.connect(dsn) as conn:
        return conn.execute(sql).fetchall()


def _monitor(client: SmartsheetClient, settings, dsn: str) -> IdMonitor:
    factory = assign_factory(settings, client, dsn)
    return IdMonitor(client, True, 60, connector_factory=factory, dsn=dsn)


async def test_processor_assigns_in_dependency_order(pilot, database) -> None:
    _seed(pilot, database)
    pilot.add(
        PROJECTS,
        2,
        provisional="KMV-ZZ-27-001",
        company="KMV",
        customer="ZZ",
        received="2027-01-05",
    )
    _new_task(pilot)
    pilot.add(RECORDS, 20, provisional=f"{NEW_TASK}-R1", task=NEW_TASK)
    pilot.add(REVISIONS, 30, provisional=f"{NEW_TASK}-V1", task=NEW_TASK)
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        monitor = _monitor(client, settings, database)
        assert monitor.mode == "assign"
        first = await monitor.run_cycle()
        # Hijos de la tarea nueva esperan a que el padre quede confirmado.
        assert first["outcomes"] == {"confirmed": 2}
        assert first["counts"]["pending_parent"] == 2
        assert pilot.stable(PROJECTS, 2) == "KMV-ZZ-27-001"
        assert pilot.stable(TASKS, 11) == NEW_TASK
        assert pilot.stable(RECORDS, 20) == ""
        second = await monitor.run_cycle()
        assert second["outcomes"] == {"confirmed": 2}
        assert pilot.stable(RECORDS, 20) == f"{NEW_TASK}-R1"
        assert pilot.stable(REVISIONS, 30) == f"{NEW_TASK}-V1"
        third = await monitor.run_cycle()
        assert third["outcomes"] == {}
        assert third["counts"] == {"already_stable": 6}
    finally:
        await client.aclose()
    # Cada PUT toca sólo la celda Stable ID de una fila.
    assert len(pilot.puts) == 4
    for sheet, body in pilot.puts:
        assert len(body) == 1 and len(body[0]["cells"]) == 1
        assert body[0]["cells"][0]["columnId"] == stable_column(sheet)
    assert _rows(database, "SELECT estado, count(*) FROM asignacion_id GROUP BY estado") == [
        ("confirmado", 6)
    ]
    audit = _rows(database, "SELECT accion, count(*) FROM auditoria_id GROUP BY accion ORDER BY 1")
    assert audit == [("confirmado", 4), ("inicializado", 2), ("reservado", 4)]


async def test_read_only_cycle_detects_pending_without_writing(pilot, database) -> None:
    _seed(pilot, database)
    _new_task(pilot)
    settings = make_settings(app_read_only=True, ids_processor_writes_enabled=True)
    client = SmartsheetClient(settings)
    try:
        monitor = _monitor(client, settings, database)
        assert monitor.mode == "simulation"
        result = await monitor.run_cycle()
        assert result["counts"] == {"already_stable": 2, "needs_reservation": 1}
        assert result["outcomes"] == {}
        with pytest.raises(ValueError, match="deshabilitada"):
            await assign_row(settings, client, database, (TASKS, 11, PROJECT), True)
    finally:
        await client.aclose()
    assert pilot.puts == []
    assert _rows(database, "SELECT count(*) FROM asignacion_id") == [(2,)]
    assert _rows(database, "SELECT count(*) FROM auditoria_id") == [(2,)]


async def test_lost_response_is_recovered_with_same_reservation(
    pilot, database, monkeypatch
) -> None:
    _seed(pilot, database)
    _new_task(pilot)
    pilot.put_failures = ["timeout"]
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    monkeypatch.setattr(id_database, "DSN", database)
    try:
        monitor = _monitor(client, settings, database)
        assert (await monitor.run_cycle())["outcomes"] == {"pending": 1}
        report = await build_dry_run_report(client, database)
        plan = plan_recovery(id_database.pending_reservations(), report)
        assert plan == [
            {
                "sheet_id": str(TASKS),
                "row_id": "11",
                "reserved_id": NEW_TASK,
                "current_action": "would_write",
                "stable_id": "",
                "recovery": "write",
            }
        ]
        assert (await monitor.run_cycle())["outcomes"] == {"confirmed": 1}
    finally:
        await client.aclose()
    assert pilot.stable(TASKS, 11) == NEW_TASK
    assert _rows(
        database, f"SELECT ultimo_numero FROM secuencia_id WHERE ambito='task:{PROJECT}'"
    ) == [(2,)]
    assert _rows(database, "SELECT count(*) FROM auditoria_id WHERE accion='reservado'") == [(1,)]


async def test_applied_write_with_server_error_confirms_after_reread(pilot, database) -> None:
    _seed(pilot, database)
    _new_task(pilot)
    pilot.put_failures = ["error_applied"]
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        result = await assign_row(settings, client, database, (TASKS, 11, PROJECT), True)
    finally:
        await client.aclose()
    assert result == {
        "sheet_id": str(TASKS),
        "row_id": "11",
        "outcome": "confirmed",
        "id": NEW_TASK,
        "state": "confirmado",
    }
    assert len(pilot.puts) == 1


async def test_automatic_resolution_never_overwrites(pilot, database) -> None:
    _seed(pilot, database)
    store = IdStore(database, allow_reservations=True, annual_policy_approved=True)
    store.reserve(TASKS, 11, EntityKind.TASK, PROJECT)
    _new_task(pilot, stable=f"{PROJECT}-07")
    pilot.add(TASKS, 12, stable=f"{PROJECT}-05", tracking=PROJECT, reference=PROJECT)
    pilot.add(TASKS, 13, provisional=f"{PROJECT}-04", tracking=PROJECT, reference=PROJECT)
    pilot.add(TASKS, 14, provisional=f"{PROJECT}-09", tracking=PROJECT, reference="OTRO")
    pilot.add(TASKS, 15, provisional=f"{PROJECT}-08", tracking=PROJECT, reference="")
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        monitor = _monitor(client, settings, database)
        report = await build_dry_run_report(client, database)
        result = await monitor.run_cycle()
        direct = await assign_row(settings, client, database, (TASKS, 11, PROJECT), True)
    finally:
        await client.aclose()
    rows = {item["row_id"]: item for item in report["pending_or_conflicting_rows"]}
    # Sin rastro se registra; número de fórmula ya ocupado se renumera; Reference vacía vale.
    assert rows["13"]["proposed_id"] == f"{PROJECT}-06" and rows["13"]["renumbered"]
    assert rows["15"]["proposed_id"] == f"{PROJECT}-08" and not rows["15"]["renumbered"]
    assert result["counts"] == {
        "already_stable": 2,
        "conflict": 2,
        "register_existing": 1,
        "needs_reservation": 2,
    }
    assert result["outcomes"] == {"registered": 1, "confirmed": 2}
    assert pilot.stable(TASKS, 12) == f"{PROJECT}-05"
    assert pilot.stable(TASKS, 13) == f"{PROJECT}-06"
    assert pilot.stable(TASKS, 15) == f"{PROJECT}-08"
    # Únicos conflictos: Stable distinto de la reserva y Reference contradictoria; no se tocan.
    assert direct["outcome"] == "conflict"
    assert pilot.stable(TASKS, 11) == f"{PROJECT}-07"
    assert pilot.stable(TASKS, 14) == ""
    assert sorted(body[0]["id"] for _, body in pilot.puts) == [13, 15]


async def test_cleared_stable_is_restored_and_new_scope_is_created(pilot, database) -> None:
    _seed(pilot, database)
    pilot.rows[TASKS][10]["Stable Task ID"] = ""
    pilot.rows[TASKS][10]["_provisional"] = f"{PROJECT}-01"
    pilot.add(
        PROJECTS,
        2,
        provisional="KMV-LP-26-001",
        company="KMV",
        customer="LP",
        received="2026-05-01",
    )
    pilot.add(
        PROJECTS,
        3,
        provisional="KMV-BS-26-453",
        company="KMV",
        customer="BS",
        received="2026-05-02",
    )
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        result = await _monitor(client, settings, database).run_cycle()
    finally:
        await client.aclose()
    assert result["outcomes"] == {"confirmed": 3}
    assert pilot.stable(TASKS, 10) == TASK
    assert pilot.stable(PROJECTS, 2) == "KMV-LP-26-001"
    assert pilot.stable(PROJECTS, 3) == "KMV-BS-26-453"
    sequences = dict(_rows(database, "SELECT ambito, ultimo_numero FROM secuencia_id"))
    assert sequences["project:KMV-LP-26"] == 1 and sequences["project:KMV-BS-26"] == 453


async def test_workspace_change_blocks_cycle_and_row(pilot, database) -> None:
    _seed(pilot, database)
    _new_task(pilot)
    pilot.workspace[TASKS] = "1234567890"
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        with pytest.raises(ValueError, match="workspace"):
            await _monitor(client, settings, database).run_cycle()
        result = await assign_row(settings, client, database, (TASKS, 11, PROJECT), True)
    finally:
        await client.aclose()
    assert result["outcome"] == "denied" and result["id"] is None
    assert pilot.puts == []


async def test_manual_assignment_requires_authorization_and_rejects_imported(
    pilot, database
) -> None:
    _seed(pilot, database)
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        with pytest.raises(ValueError, match="no autorizada"):
            await assign_row(settings, client, database, (TASKS, 11, PROJECT), False)
        with pytest.raises(ValueError, match="importado"):
            await assign_row(settings, client, database, (TASKS, 10, PROJECT), True)
        with pytest.raises(ValueError, match="no autorizados"):
            await assign_row(settings, client, database, (999, 11, PROJECT), True)
    finally:
        await client.aclose()
    assert pilot.puts == []


async def test_run_once_never_overlaps_with_active_processor(pilot, database) -> None:
    _seed(pilot, database)
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    holder = psycopg.connect(database, autocommit=True)
    try:
        holder.execute("SELECT pg_advisory_lock(%s)", (_LOCK,))
        with pytest.raises(AppError) as error:
            await _monitor(client, settings, database).run_once()
        assert error.value.code == "IDS_PROCESSOR_BUSY"
        holder.execute("SELECT pg_advisory_unlock(%s)", (_LOCK,))
        assert (await _monitor(client, settings, database).run_once())["mode"] == "assign"
    finally:
        holder.close()
        await client.aclose()


async def test_rows_inserted_above_are_numbered_in_formula_order(pilot, database) -> None:
    _seed(pilot, database)
    # Un formulario que inserta arriba deja la fila más nueva primero en pantalla.
    _new_task(pilot, provisional=f"{PROJECT}-03")
    pilot.add(TASKS, 12, provisional=NEW_TASK, tracking=PROJECT, reference=PROJECT)
    settings = make_settings(**WRITE_FLAGS)
    client = SmartsheetClient(settings)
    try:
        result = await _monitor(client, settings, database).run_cycle()
    finally:
        await client.aclose()
    assert result["outcomes"] == {"confirmed": 2}
    assert pilot.stable(TASKS, 12) == NEW_TASK
    assert pilot.stable(TASKS, 11) == f"{PROJECT}-03"
