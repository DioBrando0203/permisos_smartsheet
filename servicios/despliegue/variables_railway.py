"""Copia a Railway los ajustes de `backend/.env` (SPEC-B22 DP-02, DP-11); no imprime valores.

Pasa los interruptores e ids de hojas tal cual y fija lo propio del servidor: la base por
referencia a `Postgres`, los hosts del chequeo de salud y de la red privada. Nunca envía el
token de Smartsheet salvo con `--con-token` (decisión del usuario, DP-11); el token del ID Manager
del servidor se genera nuevo la primera vez y no se vuelve a tocar.

Uso, desde la raíz del repo con la CLI de Railway enlazada al proyecto:
`backend/.venv/bin/python servicios/despliegue/variables_railway.py [--monitor] [--con-token]`
Sin `--monitor`, el procesador queda apagado en el servidor (`IDS_MONITOR_ENABLED=false`).
"""

import argparse
import json
import secrets
import subprocess
import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[2] / "backend" / ".env"
SERVICE = "permisos_smartsheet"
TOKEN = "SMARTSHEET_ACCESS_TOKEN"
ADMIN = "IDS_ADMIN_TOKEN"
# Propias del equipo Linux o del servidor: no se copian desde el `.env`.
LOCAL_ONLY = {TOKEN, ADMIN, "IDS_DATABASE_URL", "APP_ALLOWED_HOSTS", "APP_ALLOWED_ORIGINS"}
SERVER = {
    "IDS_DATABASE_URL": "${{Postgres.DATABASE_URL}}",
    "APP_ALLOWED_HOSTS": "healthcheck.railway.app,localhost,127.0.0.1,${{RAILWAY_PRIVATE_DOMAIN}}",
}


def read_env(path: Path = ENV_FILE) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def railway(*args: str, stdin: str | None = None) -> str:
    quiet = ["--skip-deploys"] if args[0] == "set" else []
    done = subprocess.run(
        ["railway", "variable", *args, "--service", SERVICE, *quiet, "--json"],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        # El error de la CLI no trae valores de variables; igual se recorta.
        sys.exit(f"railway variable {args[0]} falló: {done.stderr.strip()[:300]}")
    return done.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--monitor", action="store_true", help="enciende el procesador")
    parser.add_argument("--con-token", action="store_true", help="envía el token (DP-11)")
    args = parser.parse_args(argv)
    env = read_env()
    wanted = {k: v for k, v in env.items() if k not in LOCAL_ONLY} | SERVER
    wanted["IDS_MONITOR_ENABLED"] = "true" if args.monitor else "false"
    railway("set", *[f"{key}={value}" for key, value in sorted(wanted.items())])
    current = json.loads(railway("list"))
    sent = sorted(wanted)
    if ADMIN not in current:
        railway("set", ADMIN, "--stdin", stdin=secrets.token_urlsafe(32))
        sent.append(f"{ADMIN} (nuevo)")
    if args.con_token:
        if not env.get(TOKEN):
            sys.exit(f"Falta {TOKEN} en backend/.env")
        railway("set", TOKEN, "--stdin", stdin=env[TOKEN])
        sent.append(TOKEN)
    print("Variables enviadas (sólo nombres): " + ", ".join(sent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
