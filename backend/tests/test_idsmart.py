"""Pruebas del contrato autenticado del ID Manager sin red real."""

import asyncio
from unittest.mock import AsyncMock, Mock

from pydantic import SecretStr

from app.services.ids import database
from tests.test_ids import database as database_fixture

TOKEN = "clave-sintetica-de-prueba"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
database_fixture = database_fixture


async def test_auth_and_swagger(make_client, smartsheet) -> None:
    client = make_client(ids_admin_token=SecretStr(TOKEN), app_read_only=True)
    assert (await client.get("/api/ids/status")).status_code == 401
    assert (
        await client.get("/api/ids/status", headers={"Authorization": "Bearer mal"})
    ).status_code == 401
    response = await client.get("/api/ids/status", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["read_only"] is True
    assert response.json()["automatic_generation_enabled"] is False
    paths = (await client.get("/openapi.json")).json()["paths"]
    for name in ("status", "database", "assignments", "audit", "dry-run", "conflicts"):
        assert f"/api/ids/{name}" in paths
    for name in ("recovery", "health", "rows/assign", "processor/run"):
        assert f"/api/ids/{name}" in paths
    status = response.json()
    assert status["smartsheet_writes_enabled"] is False
    assert status["processor_mode"] == "simulation"
    assert status["write_barriers"]["app_read_only_disabled"] is False


async def test_database_and_assignments(
    make_client, smartsheet, database_fixture, monkeypatch
) -> None:
    import psycopg

    monkeypatch.setattr(database, "DSN", database_fixture)
    with psycopg.connect(database_fixture) as conn:
        conn.execute("INSERT INTO secuencia_id VALUES ('task:P', 1)")
        conn.execute("INSERT INTO asignacion_id VALUES (1, 2, 'task:P', 1, 'ID-01', 'confirmado')")
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    summary = await client.get("/api/ids/database", headers=HEADERS)
    assert summary.json()["total_ids"] == 1
    result = await client.get(
        "/api/ids/assignments?kind=task&state=confirmado&limit=1", headers=HEADERS
    )
    assert result.json()["total"] == 1
    assert result.json()["items"][0]["fila_id"] == "2"
    assert (await client.get("/api/ids/assignments?kind=record", headers=HEADERS)).json()[
        "total"
    ] == 0


async def test_dry_run_and_conflicts(make_client, smartsheet, monkeypatch) -> None:
    import app.api.routes.idsmart as routes

    report = {
        "counts": {"conflict": 1},
        "pending_or_conflicting_rows": [
            {"action": "conflict", "row_id": "2"},
            {"action": "pending_formula", "row_id": "3"},
        ],
    }
    monkeypatch.setattr(routes, "build_dry_run_report", AsyncMock(return_value=report))
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    assert (await client.get("/api/ids/dry-run", headers=HEADERS)).json() == report
    conflicts = (await client.get("/api/ids/conflicts", headers=HEADERS)).json()
    assert conflicts["conflicts"] == [{"action": "conflict", "row_id": "2"}]
    assert all(call.request.method == "GET" for call in smartsheet.calls)


async def test_monitor_runs_without_overlap_and_stops(monkeypatch) -> None:
    import app.services.ids.monitor as module

    conn = Mock()
    conn.execute.return_value.fetchone.return_value = (True,)
    monkeypatch.setattr(module.psycopg, "connect", Mock(return_value=conn))
    preview = AsyncMock(return_value={"counts": {"already_stable": 1}})
    monkeypatch.setattr(module, "build_dry_run_report", preview)
    monitor = module.IdMonitor(AsyncMock(), True, 60)
    monitor.start()
    for _ in range(50):
        if monitor.last_run:
            break
        await asyncio.sleep(0.01)
    assert monitor.active is True
    assert monitor.last_counts == {"already_stable": 1}
    assert preview.await_count == 1
    await monitor.stop()
    assert monitor.active is False
    conn.close.assert_called_once()


async def test_monitor_refuses_second_instance(monkeypatch) -> None:
    import app.services.ids.monitor as module

    conn = Mock()
    conn.execute.return_value.fetchone.return_value = (False,)
    monkeypatch.setattr(module.psycopg, "connect", Mock(return_value=conn))
    monitor = module.IdMonitor(AsyncMock(), True, 60)
    monitor.start()
    await monitor.task
    assert monitor.active is False
    assert monitor.last_error == "processor_already_active"
    conn.close.assert_called_once()


async def test_preview_reports_conflicting_stable_cell(database_fixture, monkeypatch) -> None:
    import psycopg

    import app.services.ids.preview as preview
    from app.services.ids.formats import EntityKind
    from app.services.ids.inventory import InventorySheet
    from app.services.smartsheet import RawRow

    project = "KMV-BS-26-452"
    row = RawRow("1", 1, None, None, None, None, None, {"v": project, "s": "OTRO"})
    sheet = InventorySheet(4365321059389316, EntityKind.PROJECT, "v", "s", [row])
    with psycopg.connect(database_fixture) as conn:
        conn.execute("INSERT INTO secuencia_id VALUES ('project:KMV-BS-26', 452)")
        conn.execute(
            "INSERT INTO asignacion_id VALUES "
            "(4365321059389316, 1, 'project:KMV-BS-26', 452, %s, 'confirmado')",
            (project,),
        )
    monkeypatch.setattr(preview, "read_pilot", AsyncMock(return_value=[sheet]))
    report = await preview.build_dry_run_report(AsyncMock(), database_fixture)
    assert report["counts"]["conflict"] == 1


async def test_preview_uses_date_received_for_project_year(database_fixture, monkeypatch) -> None:
    from datetime import date

    import psycopg

    import app.services.ids.preview as preview
    from app.services.ids.formats import EntityKind
    from app.services.ids.inventory import InventorySheet
    from app.services.smartsheet import RawRow

    project = "KMV-BS-27-001"
    row = RawRow(
        "1",
        1,
        None,
        None,
        None,
        None,
        None,
        {"v": project, "s": project, "company": "KMV", "customer": "BS"},
        {"received": date(2027, 1, 5)},
    )
    sheet = InventorySheet(
        4365321059389316,
        EntityKind.PROJECT,
        "v",
        "s",
        [row],
        project_columns=("company", "customer", "received"),
    )
    with psycopg.connect(database_fixture) as conn:
        conn.execute("INSERT INTO secuencia_id VALUES ('project:KMV-BS-27', 1)")
        conn.execute(
            "INSERT INTO asignacion_id VALUES "
            "(4365321059389316, 1, 'project:KMV-BS-27', 1, %s, 'confirmado')",
            (project,),
        )
    monkeypatch.setattr(preview, "read_pilot", AsyncMock(return_value=[sheet]))
    report = await preview.build_dry_run_report(AsyncMock(), database_fixture)
    assert report["counts"]["already_stable"] == 1
    # Un ID confirmado es permanente aunque después cambie la fecha de recepción.
    row.date_cells["received"] = date(2026, 12, 31)
    report = await preview.build_dry_run_report(AsyncMock(), database_fixture)
    assert report["counts"] == {"already_stable": 1}


async def test_preview_detects_project_before_formula_exists(database_fixture, monkeypatch) -> None:
    from datetime import date

    import app.services.ids.preview as preview
    from app.services.ids.formats import EntityKind
    from app.services.ids.inventory import InventorySheet
    from app.services.smartsheet import RawRow

    row = RawRow(
        "1",
        1,
        None,
        None,
        None,
        None,
        None,
        {"company": "KMV", "customer": "BS"},
        {"received": date(2027, 1, 5)},
    )
    sheet = InventorySheet(
        4365321059389316,
        EntityKind.PROJECT,
        "v",
        "s",
        [row],
        project_columns=("company", "customer", "received"),
    )
    monkeypatch.setattr(preview, "read_pilot", AsyncMock(return_value=[sheet]))
    report = await preview.build_dry_run_report(AsyncMock(), database_fixture)
    assert report["pending_or_conflicting_rows"][0]["proposed_id"] == "KMV-BS-27-001"


async def test_assign_route_is_blocked_without_all_barriers(make_client, smartsheet) -> None:
    body = {"sheet_id": 73093952524164, "row_id": 2, "parent": "KMV-BS-26-452"}
    client = make_client(ids_admin_token=SecretStr(TOKEN), app_read_only=True)
    blocked = await client.post(
        "/api/ids/rows/assign", json=body | {"authorize_test_write": True}, headers=HEADERS
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"]["code"] == "IDS_ASSIGN_BLOCKED"
    flags = {"app_read_only": False, "ids_writes_enabled": True, "ids_transition_approved": True}
    client = make_client(ids_admin_token=SecretStr(TOKEN), **flags)
    unauthorized = await client.post("/api/ids/rows/assign", json=body, headers=HEADERS)
    assert unauthorized.status_code == 403
    assert not smartsheet.calls


async def test_processor_route_uses_shared_cycle(make_client, smartsheet, monkeypatch) -> None:
    from app.core.errors import AppError
    from app.services.ids.monitor import IdMonitor

    cycle = AsyncMock(return_value={"mode": "simulation", "counts": {}, "outcomes": {}})
    monkeypatch.setattr(IdMonitor, "run_once", cycle)
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    response = await client.post("/api/ids/processor/run", headers=HEADERS)
    assert response.json()["mode"] == "simulation"
    cycle.side_effect = AppError("IDS_PROCESSOR_BUSY", "ocupado", 409)
    assert (await client.post("/api/ids/processor/run", headers=HEADERS)).status_code == 409


async def test_audit_and_recovery_routes(
    make_client, smartsheet, database_fixture, monkeypatch
) -> None:
    import psycopg

    import app.api.routes.idsmart as routes

    monkeypatch.setattr(database, "DSN", database_fixture)
    with psycopg.connect(database_fixture) as conn:
        conn.execute("INSERT INTO secuencia_id VALUES ('task:P', 2)")
        conn.execute("INSERT INTO asignacion_id VALUES (7, 2, 'task:P', 1, 'P-01', 'reservado')")
        conn.execute("INSERT INTO asignacion_id VALUES (7, 3, 'task:P', 2, 'P-02', 'reservado')")
        conn.execute(
            "INSERT INTO auditoria_id (accion, hoja_id, fila_id, id_generado) "
            "VALUES ('reservado', 7, 2, 'P-01')"
        )
    report = {
        "counts": {},
        "pending_or_conflicting_rows": [
            {"sheet_id": "7", "row_id": "2", "action": "confirm_reservation", "stable_id": "P-01"}
        ],
    }
    monkeypatch.setattr(routes, "build_dry_run_report", AsyncMock(return_value=report))
    client = make_client(ids_admin_token=SecretStr(TOKEN))
    audit = (await client.get("/api/ids/audit?action=reservado", headers=HEADERS)).json()
    assert audit["total"] == 1 and audit["items"][0]["fila_id"] == "2"
    pending = (await client.get("/api/ids/recovery", headers=HEADERS)).json()["pending"]
    assert [item["recovery"] for item in pending] == ["confirm", "row_missing"]
