"""Reinicia el registro de IDs para empezar en 001: respalda y vacía; no toca Smartsheet.

Uso desde la raíz, con el backend detenido: `python3 servicios/ids/reiniciar_registro.py --confirmar`.
Decisión del usuario 2026-11-10 (SPEC-ID01 ID-40): se olvidan las hojas anteriores y Presentable
vuelve a numerar desde 001. Los Stable IDs de Presentable se vacían aparte, después de esto.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_PROCESSOR_LOCK = 714382002  # mismo número que `services/ids/monitor.py`
PSQL = ["sudo", "-n", "-u", "postgres", "psql", "-X", "-v", "ON_ERROR_STOP=1"]
PSQL += ["-d", "galp_servicios", "-At", "-c"]


def call(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, **kwargs)


def query(sql: str) -> str:
    return call(PSQL + [sql], capture_output=True, text=True).stdout.strip()


def counts() -> str:
    return query(
        "SELECT (SELECT count(*) FROM asignacion_id), (SELECT count(*) FROM secuencia_id), "
        "(SELECT count(*) FROM auditoria_id)"
    )


def main() -> None:
    if "--confirmar" not in sys.argv:
        raise SystemExit(
            "Borra el registro de IDs. Ejecutar con --confirmar y el backend detenido."
        )
    call(["sudo", "-v"])
    held = query(
        "SELECT count(*) FROM pg_locks WHERE locktype='advisory' "
        f"AND classid=0 AND objid={_PROCESSOR_LOCK} AND granted"
    )
    if held != "0":
        raise SystemExit(
            "El procesador de IDs está activo: detener el backend y repetir."
        )
    before = counts()
    backup_dir = Path.home() / "galp_backups"
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = backup_dir / f"galp_antes_reinicio_{stamp}.dump"
    fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as output:
        call(
            ["sudo", "-n", "-u", "postgres", "pg_dump", "-Fc", "-d", "galp_servicios"],
            stdout=output,
        )
    call(["pg_restore", "--list", str(filename)], stdout=subprocess.DEVNULL)
    query(
        "BEGIN; TRUNCATE asignacion_id, secuencia_id, auditoria_id RESTART IDENTITY; "
        "INSERT INTO estado_inicializacion_id DEFAULT VALUES ON CONFLICT DO NOTHING; COMMIT;"
    )
    after = counts()
    if (
        after != "0|0|0"
        or query("SELECT count(*) FROM estado_inicializacion_id") != "1"
    ):
        raise SystemExit(
            f"Estado inesperado tras el reinicio ({after}); revisar con el respaldo."
        )
    print(
        f"Registro reiniciado. Antes (asignaciones|secuencias|eventos): {before}; ahora: {after}."
    )
    print(f"Respaldo: {filename}")


if __name__ == "__main__":
    main()
