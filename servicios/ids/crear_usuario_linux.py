"""Crea una identidad PostgreSQL limitada; no modifica Smartsheet."""

import os
import secrets
import subprocess
from pathlib import Path


def main() -> None:
    secret_dir = Path.home() / ".config" / "galp_servicios"
    secret_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    secret_dir.chmod(0o700)
    secret_file = secret_dir / "pgpass"
    if secret_file.exists():
        raise SystemExit("Ya existe el archivo de credenciales; no se modifica.")
    query = "SELECT 1 FROM pg_roles WHERE rolname = 'galp_ids'"
    cmd = ["sudo", "-u", "postgres", "psql", "-X", "-v", "ON_ERROR_STOP=1"]
    exists = subprocess.run(
        cmd + ["-At", "-d", "postgres", "-c", query],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if exists:
        raise SystemExit("El rol galp_ids ya existe; revisar antes de continuar.")
    password = secrets.token_hex(32)
    fd = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as file:
        file.write(f"127.0.0.1:5432:galp_servicios:galp_ids:{password}\n")
    sql = f"""
BEGIN;
CREATE ROLE galp_ids LOGIN PASSWORD '{password}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
GRANT CONNECT ON DATABASE galp_servicios TO galp_ids;
GRANT USAGE ON SCHEMA public TO galp_ids;
GRANT SELECT, INSERT ON asignacion_id, estado_inicializacion_id, auditoria_id TO galp_ids;
GRANT SELECT, INSERT, UPDATE ON secuencia_id TO galp_ids;
GRANT USAGE ON SEQUENCE auditoria_id_evento_id_seq TO galp_ids;
COMMIT;
"""
    result = subprocess.run(
        cmd + ["-d", "galp_servicios"],
        input=sql,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit(
            "No se pudo crear el rol; revisar el estado de PostgreSQL y el archivo privado."
        )
    print(f"Usuario creado; credenciales privadas en {secret_file}")


if __name__ == "__main__":
    main()
