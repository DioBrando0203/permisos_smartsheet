"""Copia el registro de IDs a la base de un servidor (SPEC-B22 DP-08): mudanza sin perder nada.

Lee el origen sin modificarlo (basta el usuario `galp_ids` del equipo Linux) y escribe el
destino en una sola transacción: queda todo o nada. Antes migra el destino y exige que esté
vacío; durante la copia toma el bloqueo del procesador en las dos bases, así nadie numera a la
vez. Al final compara el contenido de cada tabla en las dos bases.

Uso, desde `backend/` en el equipo Linux con el backend apagado:
`DESTINO_URL='postgresql://...' .venv/bin/python -m app.services.ids.transfer`
(la URL va por variable de entorno para que no quede en el historial ni en la lista de procesos).
"""

import os
import sys

import psycopg
from psycopg import sql

from app.services.ids.cli import DSN
from app.services.ids.migrations import migrate

# Orden de copia: `asignacion_id` apunta a `secuencia_id`. Una tabla nueva debe sumarse aquí.
TABLES = (
    "secuencia_id",
    "estado_inicializacion_id",
    "asignacion_id",
    "auditoria_id",
    "obs_comentario",
    "id_retirado",
)
_PROCESSOR_LOCK = 714382002  # el mismo de `monitor.py`
_UTC = "-c TimeZone=UTC -c DateStyle=ISO"  # misma representación de fechas al comparar
_PUBLIC = "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"


def _lock(conn: psycopg.Connection, side: str) -> None:
    if not conn.execute("SELECT pg_try_advisory_lock(%s)", (_PROCESSOR_LOCK,)).fetchone()[0]:
        raise RuntimeError(f"El procesador está activo en la base de {side}: detenerlo antes")


def _columns(conn: psycopg.Connection, table: str) -> list[str]:
    query = (
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position"
    )
    return [row[0] for row in conn.execute(query, (table,)).fetchall()]


def fingerprint(conn: psycopg.Connection, table: str) -> tuple[int, str]:
    """(filas, huella del contenido) de una tabla; iguales en las dos bases si la copia es fiel."""
    query = sql.SQL(
        "SELECT count(*), coalesce(md5(string_agg(t::text, '|' ORDER BY t::text)), '') FROM {} t"
    ).format(sql.Identifier(table))
    count, digest = conn.execute(query).fetchone()
    return count, digest


def _check(source: psycopg.Connection, target: psycopg.Connection) -> None:
    unknown = {row[0] for row in source.execute(_PUBLIC)} - set(TABLES) - {"migracion_esquema"}
    if unknown:
        raise RuntimeError(f"Tablas sin copiar en el origen: {sorted(unknown)}; sumarlas a TABLES")
    if any(fingerprint(target, table)[0] for table in TABLES):
        raise RuntimeError("La base de destino ya tiene datos: la copia sólo va a una base vacía")


def _copy(source: psycopg.Connection, target: psycopg.Connection, table: str) -> None:
    names = sql.SQL(", ").join(sql.Identifier(name) for name in _columns(source, table))
    out = sql.SQL("COPY {} ({}) TO STDOUT").format(sql.Identifier(table), names)
    into = sql.SQL("COPY {} ({}) FROM STDIN").format(sql.Identifier(table), names)
    # COPY escribe tal cual las columnas de identidad, como `OVERRIDING SYSTEM VALUE`.
    with source.cursor().copy(out) as reader, target.cursor().copy(into) as writer:
        for block in reader:
            writer.write(block)


def _sync_identities(target: psycopg.Connection) -> None:
    """Las secuencias de identidad siguen después del último valor copiado."""
    query = (
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND is_identity = 'YES'"
    )
    for table, column in target.execute(query).fetchall():
        target.execute(
            sql.SQL(
                "SELECT setval(pg_get_serial_sequence(%s, %s), coalesce(max({c}), 1), "
                "max({c}) IS NOT NULL) FROM {t}"
            ).format(c=sql.Identifier(column), t=sql.Identifier(table)),
            (table, column),
        )


def transfer(source_dsn: str, target_dsn: str) -> dict[str, int]:
    """Filas copiadas por tabla; si algo no coincide, el destino queda como estaba."""
    migrate(target_dsn)
    with (
        psycopg.connect(source_dsn, autocommit=True, options=_UTC) as source,
        psycopg.connect(target_dsn, autocommit=True, options=_UTC) as target,
    ):
        _lock(source, "origen")
        _lock(target, "destino")
        _check(source, target)
        with source.transaction(), target.transaction():
            source.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            for table in TABLES:
                _copy(source, target, table)
            _sync_identities(target)
            expected = {table: fingerprint(source, table) for table in TABLES}
            copied = {table: fingerprint(target, table) for table in TABLES}
            if copied != expected:
                raise RuntimeError("El contenido copiado no coincide con el origen; nada se guardó")
        return {table: count for table, (count, _) in copied.items()}


def main() -> int:
    target = os.environ.get("DESTINO_URL", "").strip()
    if not target:
        print("Falta DESTINO_URL (la URL pública de la base del servidor).")
        return 2
    copied = transfer(DSN, target)
    print("Copiado y comprobado: " + ", ".join(f"{t} {n}" for t, n in copied.items()) + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
