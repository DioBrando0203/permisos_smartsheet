"""Arranque en un servidor (SPEC-B22 CA-01 a CA-05): base por URL, migraciones y puerto.

PostgreSQL temporal y datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import shutil

import pytest

psycopg = pytest.importorskip("psycopg")

from app import serve  # noqa: E402
from app.services.ids import migrations, transfer  # noqa: E402
from app.services.ids.cli import database_dsn  # noqa: E402
from tests.conftest import make_settings  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database
URL = "postgresql://servicio:clave-sintetica@db.example.internal:5432/railway"


def _fresh(dsn: str, name: str) -> str:
    """Base vacía en el mismo PostgreSQL temporal."""
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f"CREATE DATABASE {name}")
    return dsn.replace("dbname=postgres", f"dbname={name}")


def _tables(dsn: str) -> set[str]:
    with psycopg.connect(dsn) as conn:
        query = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        return {row[0] for row in conn.execute(query).fetchall()}


def _copy_sql(tmp_path, *extra: tuple[str, str]):
    folder = tmp_path / "sql"
    shutil.copytree(migrations.SQL_DIR, folder)
    for name, text in extra:
        (folder / name).write_text(text, encoding="utf-8")
    return folder


def test_the_server_database_comes_from_its_url_and_stays_secret() -> None:
    settings = make_settings(ids_database_url=URL)
    assert database_dsn(settings) == URL
    assert "clave-sintetica" not in repr(settings)
    local = database_dsn(make_settings())
    assert "host=127.0.0.1" in local and "user=galp_ids" in local
    assert database_dsn(make_settings(ids_database_url="  ")) == local


def test_listens_on_the_port_the_server_gives() -> None:
    assert serve.listen({}) == ("0.0.0.0", 8710)
    assert serve.listen({"PORT": "5123", "APP_HOST": "127.0.0.1"}) == ("127.0.0.1", 5123)


def test_without_its_database_url_nothing_starts_or_migrates(monkeypatch) -> None:
    monkeypatch.setattr(serve, "get_settings", make_settings)
    monkeypatch.setattr(migrations, "get_settings", make_settings)
    assert serve.main() == 2
    assert migrations.main([]) == 2


def test_migration_files_are_ordered_and_lose_their_own_transaction() -> None:
    versions = [version for version, _ in migrations.available()]
    assert versions[:5] == ["001", "002", "003", "004", "005"] and versions == sorted(versions)
    assert (
        migrations.body("BEGIN;\nCREATE TABLE x (a int);\ncommit;\n") == "CREATE TABLE x (a int);"
    )


async def test_a_new_database_gets_every_migration_once(database) -> None:
    fresh = _fresh(database, "nueva")
    every = [version for version, _ in migrations.available()]
    assert migrations.migrate(fresh) == every
    assert {"secuencia_id", "obs_comentario", "id_retirado", "migracion_esquema"} <= _tables(fresh)
    assert migrations.migrate(fresh) == []


async def test_a_database_from_the_linux_machine_is_registered_once(database, tmp_path) -> None:
    # La base del fixture tiene 001 a 005 aplicadas a mano, como la del equipo Linux.
    with pytest.raises(RuntimeError, match="baseline"):
        migrations.migrate(database)
    assert migrations.migrate(database, baseline="005") == []
    folder = _copy_sql(
        tmp_path, ("006_prueba.sql", "BEGIN;\nCREATE TABLE prueba (a int);\nCOMMIT;\n")
    )
    assert migrations.migrate(database, folder) == ["006"]
    assert migrations.migrate(database, folder) == [] and "prueba" in _tables(database)


async def test_a_failed_migration_leaves_nothing_half_done(database, tmp_path) -> None:
    fresh = _fresh(database, "rota")
    broken = "CREATE TABLE a_medias (a int);\nSELECT * FROM no_existe;\n"
    folder = _copy_sql(tmp_path, ("006_rota.sql", broken))
    with pytest.raises(psycopg.Error):
        migrations.migrate(fresh, folder)
    assert "a_medias" not in _tables(fresh) and "id_retirado" in _tables(fresh)
    with psycopg.connect(fresh) as conn:
        done = [row[0] for row in conn.execute("SELECT version FROM migracion_esquema")]
    assert "006" not in done and "005" in done


def _seed(dsn: str) -> None:
    """Registro sintético como el del equipo Linux: contador, IDs, auditoría y Obs."""
    with psycopg.connect(dsn) as conn:
        conn.execute("INSERT INTO secuencia_id VALUES ('project:KMV-26', 2)")
        conn.execute("INSERT INTO estado_inicializacion_id DEFAULT VALUES")
        conn.execute(
            "INSERT INTO asignacion_id VALUES "
            "(11, 1, 'project:KMV-26', 1, 'KMV-26-0001', 'confirmado'), "
            "(11, 2, 'project:KMV-26', 2, 'KMV-26-0002', 'reservado')"
        )
        conn.execute(
            "INSERT INTO auditoria_id (accion, hoja_id, fila_id, id_generado) VALUES "
            "('inicializado', NULL, NULL, NULL), ('reservado', 11, 2, 'KMV-26-0002')"
        )
        conn.execute(
            "INSERT INTO obs_comentario (comentario_id, hoja_id, fila_id) VALUES (7, 11, 1)"
        )
        conn.execute(
            "INSERT INTO id_retirado (id_generado, hoja_id, fila_id, ambito, numero, motivo) "
            "VALUES ('KMV-BS-26-001', 11, 1, 'project:KMV-BS-26', 1, 'cambio de cliente')"
        )


def test_the_registry_moves_whole_and_checked(database) -> None:
    _seed(database)
    target = _fresh(database, "servidor")
    copied = transfer.transfer(database, target)
    assert copied == {
        "secuencia_id": 1,
        "estado_inicializacion_id": 1,
        "asignacion_id": 2,
        "auditoria_id": 2,
        "obs_comentario": 1,
        "id_retirado": 1,
    }
    with psycopg.connect(target) as conn:
        # La auditoría sigue numerando después de lo copiado.
        conn.execute("INSERT INTO auditoria_id (accion) VALUES ('confirmado')")
        assert conn.execute("SELECT max(evento_id) FROM auditoria_id").fetchone()[0] == 3
    # Nunca sobre una base con datos: una segunda copia no duplica nada.
    with pytest.raises(RuntimeError, match="ya tiene datos"):
        transfer.transfer(database, target)


def test_no_copy_while_a_processor_holds_the_lock(database) -> None:
    target = _fresh(database, "ocupada")
    with psycopg.connect(database, autocommit=True) as busy:
        busy.execute("SELECT pg_advisory_lock(714382002)")
        with pytest.raises(RuntimeError, match="activo"):
            transfer.transfer(database, target)
    with psycopg.connect(target) as conn:
        assert transfer.fingerprint(conn, "asignacion_id")[0] == 0
