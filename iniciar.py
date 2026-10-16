"""Levanta el backend con un solo comando: `python3 iniciar.py` (Linux) o `py iniciar.py` (Windows).

Usa el entorno de `backend/.venv` y elige el puerto solo (ver `backend/app/launcher.py`).
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = (
    ROOT / "backend" / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
)


def main() -> int:
    if not VENV_PYTHON.is_file():
        print("Falta preparar el entorno del backend. Siga los pasos de instalación del README.")
        return 1
    if not (ROOT / "backend" / ".env").is_file():
        print("Falta backend/.env: cópielo de backend/.env.example y complete el token.")
        return 1
    try:
        return subprocess.call([str(VENV_PYTHON), "-m", "app.launcher"], cwd=ROOT / "backend")
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
