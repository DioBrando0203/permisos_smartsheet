"""Levanta el backend desde `backend/` con el entorno activado: `python run.py`.

Puerto 8710 o, si está ocupado, uno libre al azar (ver `app/launcher.py`).
"""

import sys

from app.launcher import main

if __name__ == "__main__":
    sys.exit(main())
