"""Respalda, restaura aisladamente y aplica 003 sin tocar Smartsheet."""

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


def call(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, **kwargs)


def counts(psql: list[str]) -> str:
    query = (
        "SELECT (SELECT count(*) FROM asignacion_id), "
        "(SELECT count(*) FROM secuencia_id), (SELECT count(*) FROM auditoria_id)"
    )
    return call(
        psql + ["-At", "-c", query], capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    root = Path(__file__).resolve().parent
    backup_dir = Path.home() / "galp_backups"
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup_dir.chmod(0o700)
    call(["sudo", "-v"])
    source = [
        "sudo",
        "-n",
        "-u",
        "postgres",
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-d",
        "galp_servicios",
    ]
    before = counts(source)
    filename = (
        backup_dir / f"galp_antes_003_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dump"
    )
    fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as output:
        call(
            ["sudo", "-n", "-u", "postgres", "pg_dump", "-Fc", "-d", "galp_servicios"],
            stdout=output,
        )
    call(["pg_restore", "--list", str(filename)], stdout=subprocess.DEVNULL)
    bindir = Path(
        call(["pg_config", "--bindir"], capture_output=True, text=True).stdout.strip()
    )
    with tempfile.TemporaryDirectory(prefix="galp_restore_") as temp:
        data = str(Path(temp) / "data")
        pgctl = str(bindir / "pg_ctl")
        call(
            [str(bindir / "initdb"), "-D", data, "--auth=trust"],
            stdout=subprocess.DEVNULL,
        )
        call(
            [
                pgctl,
                "-D",
                data,
                "-o",
                f"-k {temp} -c listen_addresses=",
                "-l",
                f"{temp}/log",
                "start",
            ],
            stdout=subprocess.DEVNULL,
        )
        try:
            call(
                [
                    "pg_restore",
                    "--exit-on-error",
                    "--no-owner",
                    "--no-acl",
                    "-h",
                    temp,
                    "-d",
                    "postgres",
                    str(filename),
                ]
            )
            restored = counts(
                ["psql", "-X", "-v", "ON_ERROR_STOP=1", "-h", temp, "-d", "postgres"]
            )
            if restored != before:
                raise SystemExit(
                    "Los conteos restaurados difieren; no se aplica la migración."
                )
        finally:
            call(
                [pgctl, "-D", data, "-m", "immediate", "stop"],
                stdout=subprocess.DEVNULL,
            )
    with (root / "sql/003_confirmacion.sql").open("rb") as migration:
        call(source, stdin=migration)
    if counts(source) != before:
        raise SystemExit("Los conteos cambiaron; revisar inmediatamente.")
    print("Respaldo restaurado y migración 003 aplicada; conteos conservados.")
    print(f"Respaldo: {filename}")


if __name__ == "__main__":
    main()
