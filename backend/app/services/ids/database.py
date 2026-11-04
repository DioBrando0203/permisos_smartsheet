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


def _read_only(**kwargs: object) -> psycopg.Connection:
    return psycopg.connect(
        DSN, connect_timeout=5, options="-c default_transaction_read_only=on", **kwargs
    )


def pending_reservations() -> list[tuple[int, int, str]]:
    """Reservas sin confirmar: operaciones incompletas que el procesador puede retomar."""
    try:
        with _read_only() as c:
            return c.execute(
                "SELECT hoja_id, fila_id, id_generado FROM asignacion_id "
                "WHERE estado='reservado' ORDER BY hoja_id, fila_id"
            ).fetchall()
    except psycopg.Error:
        raise AppError(
            "IDS_DATABASE_UNAVAILABLE", "No se pudo consultar PostgreSQL.", 503
        ) from None


def audit_events(limit: int, offset: int, action: str | None) -> dict:
    """Eventos de auditoría más recientes primero; no contienen nombres ni correos."""
    where, params = (" WHERE accion = %s", [action]) if action else ("", [])
    try:
        with _read_only(row_factory=dict_row) as c:
            count = c.execute("SELECT count(*) AS n FROM auditoria_id" + where, params).fetchone()
            rows = c.execute(
                "SELECT evento_id, fecha, accion, hoja_id, fila_id, id_generado FROM auditoria_id"
                + where
                + " ORDER BY evento_id DESC LIMIT %s OFFSET %s",
                [*params, limit, offset],
            ).fetchall()
    except psycopg.Error:
        raise AppError(
            "IDS_DATABASE_UNAVAILABLE", "No se pudo consultar PostgreSQL.", 503
        ) from None
    for row in rows:
        row["evento_id"] = str(row["evento_id"])
        row["fecha"] = row["fecha"].isoformat()
        row["hoja_id"] = str(row["hoja_id"]) if row["hoja_id"] else None
        row["fila_id"] = str(row["fila_id"]) if row["fila_id"] else None
    return {"items": rows, "total": count["n"], "limit": limit, "offset": offset}
