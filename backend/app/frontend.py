"""Sirve el frontend compilado (`frontend/dist`) en el puerto de la API (ADR-07 del frontend).

Las rutas del panel (`/hojas/123`, `/personas/...`) las resuelve el navegador: cualquier GET que
no sea de la API, de la documentación ni un archivo estático devuelve `index.html`.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

# backend/app/frontend.py -> backend -> raíz del proyecto
DEFAULT_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
# Rutas que nunca son del panel: un error aquí debe verse como error, no como la app.
_RESERVED = ("api", "assets", "docs", "redoc", "openapi.json")


def mount_frontend(app: FastAPI, dist: Path | None = DEFAULT_DIST) -> bool:
    """Monta el build si existe `index.html`; devuelve si quedó montado."""
    if dist is None or not (dist / "index.html").is_file():
        return False
    index = dist / "index.html"
    # Archivos sueltos del build (favicon, manifest) calculados al montar: la ruta no toca el
    # disco y no puede servir nada fuera de `dist` aunque la URL traiga `..`.
    top_files = {item.name: item for item in dist.iterdir() if item.is_file()}
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def panel(path: str) -> Response:
        if path.split("/", 1)[0] in _RESERVED:
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(top_files.get(path, index))

    return True
