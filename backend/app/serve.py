"""Arranque en un servidor (Railway u otro, SPEC-B22): migraciones y luego Uvicorn, sin recarga.

En el equipo Linux se sigue usando `python run.py` (local, ADR-B14). Aquí escucha en el puerto
que da el servidor (`PORT`) y en todas las interfaces del contenedor; quién puede llegar lo
deciden el servidor (sin dominio público, DP-06) y `APP_ALLOWED_HOSTS`. Un solo proceso: el
procesador nunca corre en más de un worker (DP-05).
"""

import os
import sys
from collections.abc import Mapping

import uvicorn

from app.core.config import get_settings
from app.services.ids.migrations import migrate

DEFAULT_PORT = 8710


def listen(environ: Mapping[str, str]) -> tuple[str, int]:
    """(interfaz, puerto) del servidor; `APP_HOST` y `PORT` los cambian."""
    return environ.get("APP_HOST") or "0.0.0.0", int(environ.get("PORT") or DEFAULT_PORT)


def main() -> int:
    url = get_settings().database_url
    if url is None:
        # Sin su base el procesador no puede numerar; mejor no arrancar que arrancar a medias.
        print("Falta IDS_DATABASE_URL: en un servidor la base no es la del equipo Linux.")
        return 2
    applied = migrate(url)
    print(f"Migraciones aplicadas: {', '.join(applied) or 'ninguna pendiente'}.", flush=True)
    host, port = listen(os.environ)
    uvicorn.run("app.main:app", host=host, port=port, workers=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
