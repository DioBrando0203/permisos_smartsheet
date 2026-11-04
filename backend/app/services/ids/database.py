"""Consultas de PostgreSQL del ID Manager; sólo lectura y errores sanitizados."""

import psycopg
from psycopg.rows import dict_row

from app.core.errors import AppError
from app.services.ids.cli import DSN


def database_summary() -> dict:
    """Conteos reales sin exponer configuración ni credenciales."""
    try:
        with psycopg.connect(
            DSN, connect_timeout=5, options="-c default_transaction_read_only=on"
        ) as c:
            total, confirmed = c.execute(
                "SELECT count(*), count(*) FILTER (WHERE estado='confirmado') FROM asignacion_id"
            ).fetchone()
            sequences = c.execute("SELECT count(*) FROM secuencia_id").fetchone()[0]
            events = c.execute("SELECT count(*) FROM auditoria_id").fetchone()[0]
            return {
                "status": "ok",
                "total_ids": total,
                "confirmed_ids": confirmed,
                "total_sequences": sequences,
                "total_events": events,
            }
    except psycopg.Error:
        raise AppError(
            "IDS_DATABASE_UNAVAILABLE", "No se pudo consultar PostgreSQL.", 503
        ) from None


def assignments(
    limit: int, offset: int, sheet_id: int | None, kind: str | None, state: str | None
) -> dict:
    """Consulta paginada y parametrizada de asignaciones."""
    conditions = []
    params = []
    if sheet_id is not None:
        conditions.append("hoja_id = %s")
        params.append(sheet_id)
    if kind is not None:
        conditions.append("split_part(ambito, ':', 1) = %s")
        params.append(kind)
    if state is not None:
        conditions.append("estado = %s")
        params.append(state)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    try:
        with psycopg.connect(
            DSN,
            connect_timeout=5,
            options="-c default_transaction_read_only=on",
            row_factory=dict_row,
        ) as c:
            count = c.execute("SELECT count(*) AS n FROM asignacion_id" + where, params).fetchone()[
                "n"
            ]
            rows = c.execute(
                "SELECT hoja_id, fila_id, ambito, numero, id_generado, estado FROM asignacion_id"
                + where
                + " ORDER BY hoja_id, fila_id LIMIT %s OFFSET %s",
                [*params, limit, offset],
            ).fetchall()
            for row in rows:
                row["hoja_id"] = str(row["hoja_id"])
                row["fila_id"] = str(row["fila_id"])
            return {"items": rows, "total": count, "limit": limit, "offset": offset}
    except psycopg.Error:
        raise AppError(
            "IDS_DATABASE_UNAVAILABLE", "No se pudo consultar PostgreSQL.", 503
        ) from None
