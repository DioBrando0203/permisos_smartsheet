from datetime import datetime

from fastapi import APIRouter, Response

from app.api.deps import ServicesDep
from app.services.sheets import SheetScope

router = APIRouter()


@router.get("/export/access.csv", response_class=Response)
async def export_access(
    services: ServicesDep, q: str | None = None, scope: SheetScope = "all"
) -> Response:
    """CSV para Excel: una fila por persona o grupo con acceso a cada hoja.

    Se genera al momento y no se guarda en el servidor. Hojas que no se pudieron leer: cabecera
    `X-Failed-Sheets` con su cantidad.
    """
    content, failed = await services.export.access_csv(q, scope)
    name = f"accesos-smartsheet-{datetime.now():%Y-%m-%d}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{name}"',
        "X-Failed-Sheets": str(len(failed)),
        "Cache-Control": "no-store",
    }
    return Response(content=content, media_type="text/csv; charset=utf-8", headers=headers)
