"""Traslado del registro a otra hoja maestra (PEN-48): plan puro y transacción en PostgreSQL.

Datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import pytest

psycopg = pytest.importorskip("psycopg")

from app.services.ids.rehome import Move, apply_moves, plan_moves  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database
OLD, NEW = 100, 200


def test_plan_moves_each_copy_mother_to_its_registered_row() -> None:
    registered = {"KMV-BS-26-001": 1, "KMV-CC-26-002": 3, "KMV-BS-26-004": 9}
    origin = [("KMV-BS-26-001", 1), ("KMV-CC-26-002", 3)]
    destination = [("KMV-CC-26-002", 30), ("KMV-BS-26-001", 10)]
    assert plan_moves(registered, origin, destination) == [
        Move("KMV-BS-26-001", 1, 10),
        Move("KMV-CC-26-002", 3, 30),
    ]


def test_plan_rejects_ambiguity_without_partial_moves() -> None:
    registered = {"KMV-BS-26-001": 1}
    origin = [("KMV-BS-26-001", 1)]
    with pytest.raises(ValueError, match="repite"):
        plan_moves(registered, origin, [("KMV-BS-26-001", 10), ("KMV-BS-26-001", 11)])
    with pytest.raises(ValueError, match="no está registrado"):
        plan_moves(registered, origin, [("KMV-BS-26-002", 10)])
    with pytest.raises(ValueError, match="fila registrada"):
        plan_moves(registered, [("KMV-BS-26-001", 5)], [("KMV-BS-26-001", 10)])


def _seed(dsn: str) -> None:
    with psycopg.connect(dsn) as conn:
        conn.execute("INSERT INTO estado_inicializacion_id DEFAULT VALUES")
        conn.execute("INSERT INTO secuencia_id VALUES ('project:KMV-BS-26', 4)")
        for row, number in ((1, 1), (2, 4)):
            conn.execute(
                "INSERT INTO asignacion_id VALUES "
                "(%s, %s, 'project:KMV-BS-26', %s, %s, 'confirmado')",
                (OLD, row, number, f"KMV-BS-26-00{number}"),
            )


def _rows(dsn: str, sql: str) -> list:
    with psycopg.connect(dsn) as conn:
        return conn.execute(sql).fetchall()


def test_apply_moves_registry_audits_and_marks_comments(database) -> None:
    _seed(database)
    apply_moves(database, OLD, NEW, [Move("KMV-BS-26-001", 1, 10)], [(555, 10), (556, 10)])
    assignments = "SELECT hoja_id, fila_id, id_generado, estado FROM asignacion_id ORDER BY 3"
    assert _rows(database, assignments) == [
        (NEW, 10, "KMV-BS-26-001", "confirmado"),
        (OLD, 2, "KMV-BS-26-004", "confirmado"),  # fila borrada: sigue reservando su número
    ]
    assert _rows(database, "SELECT ultimo_numero FROM secuencia_id") == [(4,)]
    assert _rows(database, "SELECT accion, hoja_id, fila_id FROM auditoria_id") == [
        ("inicializado", NEW, 10)
    ]
    assert _rows(database, "SELECT comentario_id FROM obs_comentario ORDER BY 1") == [
        (555,),
        (556,),
    ]


def test_apply_refuses_while_processor_holds_its_lock(database) -> None:
    _seed(database)
    with psycopg.connect(database, autocommit=True) as processor:
        processor.execute("SELECT pg_advisory_lock(714382002)")
        with pytest.raises(RuntimeError, match="detener el backend"):
            apply_moves(database, OLD, NEW, [Move("KMV-BS-26-001", 1, 10)], [])
    assert _rows(database, "SELECT hoja_id FROM asignacion_id WHERE fila_id=1") == [(OLD,)]
