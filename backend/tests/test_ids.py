"""Pruebas de IDs con PostgreSQL temporal, sin Smartsheet ni datos reales."""

import asyncio
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

psycopg = pytest.importorskip("psycopg")

from app.services.ids import (  # noqa: E402
    EntityKind,
    ExistingId,
    IdStore,
    cli,  # noqa: E402
    make_id,
    parse_id,
)
from app.services.ids.connector import (  # noqa: E402
    IdConnector,
    Outcome,
    Snapshot,
    Target,
    WriteUncertain,
)
from app.services.ids.dry_run import PILOT_WORKSPACE  # noqa: E402
from app.services.ids.inventory import InventorySheet  # noqa: E402
from app.services.smartsheet import RawRow  # noqa: E402
from tests.conftest import make_settings  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BIN = Path("/usr/lib/postgresql/18/bin")
TEST_STARTS = {
    "project:KMV-BS-26": 1,
    "project:KMV-CC-26": 1,
    "task:KMV-BS-26-452": 1,
    "record:KMV-BS-26-452-02": 1,
    "revision:KMV-BS-26-452-02": 1,
}


@pytest.fixture
def database(tmp_path):
    if not (BIN / "initdb").exists() or os.geteuid() == 0:
        pytest.skip("Se requiere PostgreSQL 18 local y usuario no root")
    data = tmp_path / "data"
    subprocess.run(
        [str(BIN / "initdb"), "-D", str(data), "--auth=trust"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            str(BIN / "pg_ctl"),
            "-D",
            str(data),
            "-o",
            f"-k {tmp_path} -c listen_addresses=",
            "-l",
            str(tmp_path / "log"),
            "start",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    dsn = f"host={tmp_path} dbname=postgres"
    try:
        with psycopg.connect(dsn) as conn:
            conn.execute("CREATE ROLE galp_ids")
            for filename in (
                "001_esquema.sql",
                "002_auditoria_inicializacion.sql",
                "003_confirmacion.sql",
            ):
                sql = (ROOT / "servicios/ids/sql" / filename).read_text()
                conn.execute(sql)
        yield dsn
    finally:
        subprocess.run(
            [str(BIN / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"],
            check=True,
            stdout=subprocess.DEVNULL,
        )


def test_formats() -> None:
    assert make_id(EntityKind.PROJECT, "KMV-BS-26", 452) == "KMV-BS-26-452"
    assert make_id(EntityKind.TASK, "KMV-BS-26-452", 2) == "KMV-BS-26-452-02"
    assert make_id(EntityKind.RECORD, "KMV-BS-26-452-02", 1).endswith("-R1")
    assert parse_id(EntityKind.REVISION, "KMV-BS-26-452-02-V1").number == 1
    with pytest.raises(ValueError):
        parse_id(EntityKind.RECORD, "KMV-BS-26-452-02-R01")


def test_initialization_atomic_and_idempotent(database) -> None:
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    with pytest.raises(ValueError):
        store.reserve(1, 2, EntityKind.PROJECT, "KMV-BS-26")
    existing = ExistingId(1, 1, EntityKind.PROJECT, "KMV-BS-26-452")
    with pytest.raises(ValueError):
        store.initialize([existing, existing])
    store.initialize([existing])
    store.initialize([existing])
    with pytest.raises(ValueError):
        store.initialize([ExistingId(1, 1, EntityKind.PROJECT, "KMV-BS-26-453")])
    reservation = store.reserve(1, 2, EntityKind.PROJECT, "KMV-BS-26")
    assert reservation.value == "KMV-BS-26-453"
    assert store.reserve(1, 2, EntityKind.PROJECT, "KMV-BS-26") == reservation
    with pytest.raises(ValueError):
        store.reserve(1, 2, EntityKind.PROJECT, "KMV-CC-26")
    with psycopg.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM auditoria_id").fetchone()[0] == 2


def test_concurrent_reservations(database) -> None:
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([ExistingId(1, 1, EntityKind.TASK, "KMV-BS-26-452-02")])
    with ThreadPoolExecutor(max_workers=12) as pool:
        same = list(
            pool.map(lambda _: store.reserve(1, 2, EntityKind.TASK, "KMV-BS-26-452"), range(24))
        )
        different = list(
            pool.map(lambda n: store.reserve(1, n, EntityKind.TASK, "KMV-BS-26-452"), range(3, 23))
        )
    assert {item.value for item in same} == {"KMV-BS-26-452-03"}
    assert len({item.value for item in different}) == 20
    assert store.reserve(2, 1, EntityKind.RECORD, "KMV-BS-26-452-02").value.endswith("-R1")
    assert store.reserve(3, 1, EntityKind.REVISION, "KMV-BS-26-452-02").value.endswith("-V1")


def test_historical_maximum_in_initialization(database) -> None:
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize(
        [ExistingId(1, 1, EntityKind.PROJECT, "KMV-BS-26-452")],
        historical=[(EntityKind.PROJECT, "KMV-BS-26-499")],
    )
    assert store.reserve(1, 2, EntityKind.PROJECT, "KMV-BS-26").value == "KMV-BS-26-500"


async def test_import_is_repeatable_and_simulation_does_not_mutate(database, monkeypatch) -> None:
    raw = RawRow("1", 1, None, None, None, None, None, {"v": "KMV-BS-26-452", "s": "KMV-BS-26-452"})
    sheet = InventorySheet(1, EntityKind.PROJECT, "v", "s", [raw])
    monkeypatch.setattr(cli, "DSN", database)
    monkeypatch.setattr(cli, "Settings", lambda: make_settings(app_read_only=True))
    monkeypatch.setattr(cli, "SmartsheetClient", lambda _: AsyncMock())
    monkeypatch.setattr(cli, "read_pilot", AsyncMock(return_value=[sheet]))
    await cli.run("importar")
    await cli.run("importar")
    with psycopg.connect(database) as conn:
        before = conn.execute("SELECT count(*) FROM auditoria_id").fetchone()[0]
        sequences = conn.execute("SELECT * FROM secuencia_id").fetchall()
    await cli.run("dry-run")
    with psycopg.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM auditoria_id").fetchone()[0] == before == 1
        assert conn.execute("SELECT * FROM secuencia_id").fetchall() == sequences


async def test_simulation_proposes_new_task_and_reuses_reservation(database, monkeypatch, capsys):
    project_id, task_id = 4365321059389316, 73093952524164
    project = ExistingId(project_id, 1, EntityKind.PROJECT, "KMV-BS-26-452")
    task = ExistingId(task_id, 2, EntityKind.TASK, "KMV-BS-26-452-02")
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([project, task])
    pending = RawRow(
        "3",
        3,
        None,
        None,
        None,
        None,
        None,
        {"v": "", "s": "", "p": project.value, "ref": project.value},
    )
    sheet = InventorySheet(task_id, EntityKind.TASK, "v", "s", [pending], "p", "ref")
    monkeypatch.setattr(cli, "DSN", database)
    await cli._simulate([sheet], [project, task])
    output = capsys.readouterr().out
    assert "KMV-BS-26-452-03" in output
    with psycopg.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM asignacion_id").fetchone()[0] == 2
    store.reserve(task_id, 3, EntityKind.TASK, project.value)
    await cli._simulate([sheet], [project, task])
    assert "KMV-BS-26-452-03" in capsys.readouterr().out
    with psycopg.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM asignacion_id").fetchone()[0] == 3


async def test_connector_recovers_lost_response_and_never_overwrites(database) -> None:
    from dataclasses import replace

    task_sheet = 73093952524164
    parent = "KMV-BS-26-452"
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([ExistingId(task_sheet, 1, EntityKind.TASK, f"{parent}-02")])
    target = Target(task_sheet, 2, EntityKind.TASK, parent)

    class Gateway:
        snapshot = Snapshot(PILOT_WORKSPACE, parent, True, f"{parent}-03", "")
        writes = 0

        async def read(self, target):
            return self.snapshot

        async def write_if_unchanged(self, target, previous, value):
            if self.snapshot != previous:
                return False
            self.writes += 1
            self.snapshot = replace(self.snapshot, stable=value)
            raise WriteUncertain()

    gateway = Gateway()
    blocked = IdConnector(store, gateway, read_only=True)
    assert await blocked.process(target) == Outcome.READ_ONLY
    assert store.lookup(task_sheet, 2) is None
    connector = IdConnector(store, gateway, read_only=False)
    assert await connector.process(target) == Outcome.CONFIRMED
    assert await connector.process(target) == Outcome.CONFIRMED
    assert gateway.writes == 1
    assert store.lookup(task_sheet, 2).state == "confirmado"
    with psycopg.connect(database) as conn:
        assert (
            conn.execute("SELECT count(*) FROM auditoria_id WHERE accion='confirmado'").fetchone()[
                0
            ]
            == 1
        )


async def test_network_failure_retains_reservation_for_retry(database) -> None:
    from dataclasses import replace

    task_sheet, parent = 73093952524164, "KMV-BS-26-452"
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([ExistingId(task_sheet, 1, EntityKind.TASK, f"{parent}-02")])

    class Gateway:
        snapshot = Snapshot(PILOT_WORKSPACE, parent, True, f"{parent}-03", "")
        attempts = 0

        async def read(self, target):
            return self.snapshot

        async def write_if_unchanged(self, target, previous, value):
            self.attempts += 1
            if self.attempts == 1:
                raise WriteUncertain()
            self.snapshot = replace(self.snapshot, stable=value)
            return True

    gateway = Gateway()
    connector = IdConnector(store, gateway, read_only=False)
    target = Target(task_sheet, 2, EntityKind.TASK, parent)
    assert await connector.process(target) == Outcome.PENDING
    assert store.lookup(task_sheet, 2).value == f"{parent}-03"
    assert await connector.process(target) == Outcome.CONFIRMED
    with psycopg.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM asignacion_id").fetchone()[0] == 2
    gateway.snapshot = replace(gateway.snapshot, stable="OTRO")
    assert await connector.process(target) == Outcome.CONFLICT
    assert gateway.attempts == 2


async def test_connector_assigns_when_formula_is_still_empty(database) -> None:
    from dataclasses import replace

    task_sheet, parent = 73093952524164, "KMV-BS-26-452"
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([ExistingId(task_sheet, 1, EntityKind.TASK, f"{parent}-02")])

    class Gateway:
        snapshot = Snapshot(PILOT_WORKSPACE, parent, True, "", "")

        async def read(self, target):
            return self.snapshot

        async def write_if_unchanged(self, target, previous, value):
            self.snapshot = replace(self.snapshot, stable=value)
            return True

    connector = IdConnector(store, Gateway(), read_only=False)
    assert (
        await connector.process(Target(task_sheet, 2, EntityKind.TASK, parent)) == Outcome.CONFIRMED
    )
    assert store.lookup(task_sheet, 2).value == f"{parent}-03"


def test_reservations_require_approved_scope_and_respect_start(database) -> None:
    initial = ExistingId(1, 1, EntityKind.PROJECT, "KMV-BS-26-452")
    store = IdStore(database, allow_reservations=True)
    store.initialize([initial])
    with pytest.raises(ValueError):
        store.reserve(1, 2, EntityKind.PROJECT, "KMV-BS-26")
    approved = IdStore(
        database, allow_reservations=True, approved_starts={"project:KMV-BS-26": 900}
    )
    assert approved.reserve(1, 2, EntityKind.PROJECT, "KMV-BS-26").value == "KMV-BS-26-900"
    assert approved.reserve(1, 3, EntityKind.PROJECT, "KMV-BS-26").value == "KMV-BS-26-901"


def test_confirmation_migration_is_repeatable_and_preserves_assignments(database) -> None:
    store = IdStore(database)
    store.initialize([ExistingId(1, 1, EntityKind.PROJECT, "KMV-BS-26-452")])
    migration = (ROOT / "servicios/ids/sql/003_confirmacion.sql").read_text()
    with psycopg.connect(database) as conn:
        conn.execute(migration)
        assert conn.execute("SELECT count(*) FROM asignacion_id").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM auditoria_id").fetchone()[0] == 1


async def test_connector_rejects_wrong_workspace_and_formula(database) -> None:
    task_sheet = 73093952524164
    parent = "KMV-BS-26-452"
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([ExistingId(task_sheet, 1, EntityKind.TASK, f"{parent}-02")])
    gateway = AsyncMock()
    gateway.read.return_value = Snapshot("otro", parent, True, f"{parent}-03", "")
    connector = IdConnector(store, gateway, read_only=False)
    target = Target(task_sheet, 2, EntityKind.TASK, parent)
    assert await connector.process(target) == Outcome.DENIED
    assert store.lookup(task_sheet, 2) is None
    gateway.read.return_value = Snapshot(PILOT_WORKSPACE, parent, True, f"{parent}-05", "")
    assert await connector.process(target) == Outcome.CONFLICT
    gateway.write_if_unchanged.assert_not_called()


async def test_connector_concurrent_calls_share_one_reservation(database) -> None:
    from dataclasses import replace

    task_sheet, parent = 73093952524164, "KMV-BS-26-452"
    store = IdStore(database, allow_reservations=True, approved_starts=TEST_STARTS)
    store.initialize([ExistingId(task_sheet, 1, EntityKind.TASK, f"{parent}-02")])

    class Gateway:
        snapshot = Snapshot(PILOT_WORKSPACE, parent, True, f"{parent}-03", "")
        writes = 0

        async def read(self, target):
            return self.snapshot

        async def write_if_unchanged(self, target, previous, value):
            if self.snapshot != previous:
                return False
            self.writes += 1
            self.snapshot = replace(self.snapshot, stable=value)
            return True

    gateway = Gateway()
    connector = IdConnector(store, gateway, read_only=False)
    target = Target(task_sheet, 2, EntityKind.TASK, parent)
    results = await asyncio.gather(*(connector.process(target) for _ in range(8)))
    assert all(
        result in (Outcome.CONFIRMED, Outcome.CONFLICT, Outcome.PENDING) for result in results
    )
    assert Outcome.CONFIRMED in results
    assert gateway.writes == 1
    with psycopg.connect(database) as conn:
        assert conn.execute("SELECT count(*) FROM asignacion_id").fetchone()[0] == 2
        assert (
            conn.execute("SELECT count(*) FROM auditoria_id WHERE accion='confirmado'").fetchone()[
                0
            ]
            == 1
        )
