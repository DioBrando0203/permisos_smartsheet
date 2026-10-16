"""Arranque del backend sin escribir el puerto: 8710 si está libre, si no uno libre al azar.

Lo usa `run.py` (desde `backend/`, con el entorno activado). El puerto elegido se pasa a la
app como `APP_PORT` para que sus orígenes se permitan (Swagger escribe desde ese mismo
puerto, ADR-B08).
"""

import os
import signal
import socket
import subprocess
import sys
from pathlib import Path

PREFERRED_PORT = 8710
HOST = "127.0.0.1"
BACKEND_DIR = Path(__file__).resolve().parents[1]
# Puerto real para el proxy de Vite en desarrollo (ADR-07 del frontend); no se versiona.
PORT_FILE = BACKEND_DIR / ".port"


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


def write_port_file(port: int, path: Path = PORT_FILE) -> None:
    path.write_text(f"{port}\n", encoding="utf-8")


def remove_port_file(port: int, path: Path = PORT_FILE) -> None:
    """Borra el archivo sólo si sigue siendo de este arranque (otro pudo reemplazarlo)."""
    try:
        if path.read_text(encoding="utf-8").strip() == str(port):
            path.unlink()
    except FileNotFoundError:
        return


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
    # Un cierre por señal (terminal cerrada, `kill`) también debe limpiar: SystemExit lleva al
    # `finally`, que detiene Uvicorn con orden y borra `.port`.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    write_port_file(port)
    process = subprocess.Popen(command, cwd=BACKEND_DIR, env=env)
    try:
        return process.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        stop(process)
        remove_port_file(port)


def stop(process: subprocess.Popen[bytes], timeout: float = 10.0) -> None:
    """Pide a Uvicorn que termine (él cierra su proceso de recarga) y sólo si no responde, lo mata.

    Matarlo de golpe deja huérfano al proceso que atiende el puerto y el puerto queda ocupado.
    """
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


if __name__ == "__main__":
    sys.exit(main())
