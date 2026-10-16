"""Arranque del backend sin escribir el puerto: 8710 si está libre, si no uno libre al azar.

Lo usa `iniciar.py` en la raíz. El puerto elegido se pasa a la app como `APP_PORT` para que
sus orígenes se permitan (Swagger escribe desde ese mismo puerto, ADR-B08).
"""

import os
import socket
import subprocess
import sys
from pathlib import Path

PREFERRED_PORT = 8710
HOST = "127.0.0.1"
BACKEND_DIR = Path(__file__).resolve().parents[1]


def is_free(port: int, host: str = HOST) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def pick_port(preferred: int = PREFERRED_PORT, host: str = HOST) -> int:
    """El preferido si está libre; si no, uno que el sistema asigne libre."""
    if is_free(preferred, host):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return probe.getsockname()[1]


def main() -> int:
    port = pick_port()
    if port != PREFERRED_PORT:
        print(f"El puerto {PREFERRED_PORT} está ocupado; se usa el {port}.")
    print(f"Backend: http://{HOST}:{port}/docs  (Ctrl+C para detener)", flush=True)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--env-file",
        ".env",
        "--host",
        HOST,
        "--port",
        str(port),
        "--reload",
    ]
    env = os.environ | {"APP_PORT": str(port)}
    try:
        return subprocess.call(command, cwd=BACKEND_DIR, env=env)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
