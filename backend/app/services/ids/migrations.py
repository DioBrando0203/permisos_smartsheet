"""Migraciones de la base del servicio en un servidor (SPEC-B22 DP-04).

Los mismos archivos `servicios/ids/sql/NNN_nombre.sql` que en el equipo Linux (B-16) se aplican
a mano con respaldo. En un servidor se aplican al arrancar, en orden, cada uno una sola vez y con
su registro en `migracion_esquema` dentro de la misma transacción. Una base traída de B-16 ya
tiene aplicadas las suyas: se registran una vez con `--baseline NNN`, sin volver a ejecutarlas.

Uso manual (sólo contra una base de servidor): `python -m app.services.ids.migrations`.
"""

import argparse
import re
import sys
from pathlib import Path

import psycopg

from app.core.config import get_settings

SQL_DIR = Path(__file__).resolve().parents[4] / "servicios" / "ids" / "sql"
_LOCK = 714382003  # distinto del procesador (714382002): dos arranques no migran a la vez
_NAME = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")
_TABLE = (
    "CREATE TABLE IF NOT EXISTS migracion_esquema ("
    "version text PRIMARY KEY, archivo text NOT NULL, "
    "aplicada timestamptz NOT NULL DEFAULT now())"
)
# Los archivos dan permisos al usuario del servicio en B-16; en una base nueva debe existir.
_ROLE = (
    "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'galp_ids') "
    "THEN CREATE ROLE galp_ids NOLOGIN; END IF; END $$"
)
_RECORD = "INSERT INTO migracion_esquema (version, archivo) VALUES (%s, %s)"


def available(directory: Path = SQL_DIR) -> list[tuple[str, Path]]:
    """(versión, archivo) en orden; un nombre fuera de formato o una versión repetida es error."""
    found = []
    for path in sorted(directory.glob("*.sql")):
        match = _NAME.match(path.name)
        if match is None:
            raise ValueError(f"Migración con nombre inválido: {path.name}")
        found.append((match.group(1), path))
    versions = [version for version, _ in found]
    if len(set(versions)) != len(versions):
        raise ValueError("Versiones de migración repetidas")
    return found


def body(sql: str) -> str:
    """Sin las líneas `BEGIN;` y `COMMIT;` de los archivos: la transacción la abre el aplicador."""
    return "\n".join(
        line for line in sql.splitlines() if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )


def migrate(dsn: str, directory: Path = SQL_DIR, baseline: str | None = None) -> list[str]:
    """Aplica las pendientes y devuelve sus versiones; con `baseline`, registra sin ejecutar
    las que ya trae la base hasta esa versión."""
    files = available(directory)
    with psycopg.connect(dsn, autocommit=True, connect_timeout=10) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (_LOCK,))
        tracked = conn.execute("SELECT to_regclass('migracion_esquema') IS NOT NULL").fetchone()
        manual = conn.execute("SELECT to_regclass('secuencia_id') IS NOT NULL").fetchone()
        if not tracked[0] and manual[0] and baseline is None:
            raise RuntimeError(
                "La base ya tiene migraciones aplicadas a mano: registrarlas una vez con --baseline"
            )
        conn.execute(_ROLE)
        conn.execute(_TABLE)
        done = {row[0] for row in conn.execute("SELECT version FROM migracion_esquema")}
        applied = []
        for version, path in files:
            if version in done:
                continue
            with conn.transaction():
                if baseline is None or version > baseline:
                    conn.execute(body(path.read_text(encoding="utf-8")))
                    applied.append(version)
                conn.execute(_RECORD, (version, path.name))
        return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migraciones de la base del servicio (SPEC-B22).")
    parser.add_argument(
        "--baseline",
        help="registra como aplicadas, sin ejecutarlas, las versiones hasta esta (base de B-16)",
    )
    args = parser.parse_args(argv)
    url = get_settings().database_url
    if url is None:
        print("Falta IDS_DATABASE_URL: en el equipo Linux las migraciones siguen a mano.")
        return 2
    applied = migrate(url, baseline=args.baseline)
    print(f"Migraciones aplicadas: {', '.join(applied) or 'ninguna pendiente'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
