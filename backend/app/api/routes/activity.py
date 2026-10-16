from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import ServicesDep, SheetId
from app.models.activity import RowHistory, SheetActivity

router = APIRouter()

RowId = Annotated[str, Path(pattern=r"^\d{1,20}$", description="Id de la fila")]


@router.get("/{sheet_id}/activity")
async def sheet_activity(
    services: ServicesDep,
    sheet_id: SheetId,
    days: Annotated[int, Query(ge=1, le=3650)] = 30,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    refresh: bool = False,
) -> SheetActivity:
    """Filas modificadas en los últimos `days` días, quién edita y quién tiene edición sin usarla.

    Datos directos de Smartsheet (última modificación de cada fila). Ver `limitations`.
    """
    return await services.activity.activity(sheet_id, days, limit, refresh=refresh)


@router.get("/{sheet_id}/rows/{row_id}/history")
async def row_history(
    services: ServicesDep,
    sheet_id: SheetId,
    row_id: RowId,
    column_id: Annotated[str | None, Query(pattern=r"^\d{1,20}$")] = None,
) -> RowHistory:
    """Historial de cambios de una fila (columnas con valor) o de una celda (`column_id`)."""
    return await services.activity.row_history(sheet_id, row_id, column_id)
