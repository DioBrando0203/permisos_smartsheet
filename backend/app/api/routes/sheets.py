from fastapi import APIRouter, Response, status

from app.api.deps import ServicesDep, ShareId, SheetId
from app.models.shares import Share, ShareCreate, ShareCreateResult, ShareList, ShareUpdate
from app.models.sheets import SheetList, SheetSummary

router = APIRouter()


@router.get("")
async def list_sheets(
    services: ServicesDep, q: str | None = None, refresh: bool = False
) -> SheetList:
    """Hojas accesibles por el token, por nombre; `q` filtra sin tildes ni mayúsculas."""
    return await services.sheets.list(q, refresh=refresh)


@router.get("/{sheet_id}")
async def get_sheet(services: ServicesDep, sheet_id: SheetId) -> SheetSummary:
    return await services.sheets.get(sheet_id)


@router.get("/{sheet_id}/shares")
async def list_shares(services: ServicesDep, sheet_id: SheetId, refresh: bool = False) -> ShareList:
    """Quién tiene acceso a la hoja: propios y heredados del workspace."""
    return await services.shares.list(sheet_id, refresh=refresh)


@router.post("/{sheet_id}/shares", status_code=status.HTTP_201_CREATED)
async def create_shares(
    services: ServicesDep, sheet_id: SheetId, body: ShareCreate
) -> ShareCreateResult:
    """Dar acceso a uno o varios correos o grupos. Sin correo de aviso salvo `send_email`."""
    return await services.shares.create(sheet_id, body)


@router.patch("/{sheet_id}/shares/{share_id}")
async def update_share(
    services: ServicesDep, sheet_id: SheetId, share_id: ShareId, body: ShareUpdate
) -> Share:
    """Cambiar el nivel de un acceso propio de la hoja."""
    return await services.shares.update(sheet_id, share_id, body.access_level)


@router.delete("/{sheet_id}/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share(services: ServicesDep, sheet_id: SheetId, share_id: ShareId) -> Response:
    """Quitar un acceso propio de la hoja."""
    await services.shares.delete(sheet_id, share_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
