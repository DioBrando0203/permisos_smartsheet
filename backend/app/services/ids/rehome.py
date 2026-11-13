"""Traslado del registro de IDs a otra hoja maestra (PEN-48): mismos números, otras filas.

Una copia de la maestra lleva los mismos Stable IDs en filas nuevas. El registro de cada madre
pasa de su fila original a la fila de la copia con el mismo ID: no crea, cambia ni reutiliza
números. Los comentarios que ya trae la copia se marcan como incorporados a Obs para no
duplicarlos. Exige el procesador detenido (su bloqueo global en PostgreSQL).
"""

from dataclasses import dataclass

import psycopg

_PROCESSOR_LOCK = 714382002  # mismo número que `services/ids/monitor.py`


@dataclass(frozen=True)
class Move:
    value: str
    old_row: int
    new_row: int


def plan_moves(
    registered: dict[str, int],
    origin: list[tuple[str, int]],
    destination: list[tuple[str, int]],
) -> list[Move]:
    """Traslados de cada madre de la copia; falla ante cualquier ambigüedad, sin traslado parcial.

    `registered`: Stable ID -> fila registrada en la hoja de origen. `origin` y `destination`:
    pares (Stable ID, fila) de las madres con Stable ID de cada hoja.
    """
    current = _unique(origin, "origen")
    copies = _unique(destination, "copia")
    moves = []
    for value, new_row in sorted(copies.items()):
        if registered.get(value) is None:
            raise ValueError(f"{value} no está registrado en la hoja de origen")
        if current.get(value) != registered[value]:
            raise ValueError(f"{value} no está en la fila registrada de la hoja de origen")
        moves.append(Move(value, registered[value], new_row))
    return moves


def apply_moves(
    dsn: str,
    origin_sheet: int,
    destination_sheet: int,
    moves: list[Move],
    comments: list[tuple[int, int]],
) -> None:
    """Una sola transacción: traslada asignaciones, audita `inicializado` y marca comentarios.

    `comments`: pares (comentario, fila) ya presentes en la copia.
    """
    with psycopg.connect(dsn, connect_timeout=5) as conn:
        locked = conn.execute("SELECT pg_try_advisory_lock(%s)", (_PROCESSOR_LOCK,)).fetchone()
        if not locked[0]:
            raise RuntimeError("El procesador de IDs está activo: detener el backend antes")
        for move in moves:
            row = conn.execute(
                "SELECT ambito, numero, estado FROM asignacion_id "
                "WHERE hoja_id=%s AND fila_id=%s AND id_generado=%s FOR UPDATE",
                (origin_sheet, move.old_row, move.value),
            ).fetchone()
            if row is None:
                raise ValueError(f"{move.value} cambió en el registro durante el traslado")
            conn.execute(
                "DELETE FROM asignacion_id WHERE hoja_id=%s AND fila_id=%s",
                (origin_sheet, move.old_row),
            )
            conn.execute(
                "INSERT INTO asignacion_id VALUES (%s, %s, %s, %s, %s, %s)",
                (destination_sheet, move.new_row, row[0], row[1], move.value, row[2]),
            )
            conn.execute(
                "INSERT INTO auditoria_id (accion, hoja_id, fila_id, id_generado) "
                "VALUES ('inicializado', %s, %s, %s)",
                (destination_sheet, move.new_row, move.value),
            )
        conn.cursor().executemany(
            "INSERT INTO obs_comentario (comentario_id, hoja_id, fila_id) VALUES (%s, %s, %s) "
            "ON CONFLICT (comentario_id) DO NOTHING",
            [(comment, destination_sheet, row) for comment, row in comments],
        )


def _unique(pairs: list[tuple[str, int]], label: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for value, row in pairs:
        if value in result:
            raise ValueError(f"{value} se repite en la hoja de {label}")
        result[value] = row
    return result
