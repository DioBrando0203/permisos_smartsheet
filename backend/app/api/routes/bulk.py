from fastapi import APIRouter

from app.api.deps import ServicesDep, SheetId
from app.models.bulk import CopyPlan, CopyRequest, RevokePlan, RevokeRequest

router = APIRouter()


@router.post("/sheets/{sheet_id}/shares/copy")
async def copy_shares(services: ServicesDep, sheet_id: SheetId, body: CopyRequest) -> CopyPlan:
    """Copiar los accesos de `source_sheet_id` a esta hoja (destino).

    Por defecto sólo simula (`dry_run=true`). Nunca baja ni quita a nadie; `OWNER` se copia
    como `ADMIN`. Ejecutar exige `dry_run=false` y `APP_READ_ONLY=false`.
    """
    return await services.bulk.copy(sheet_id, body)


@router.post("/users/{key}/revoke")
async def revoke_person(services: ServicesDep, key: str, body: RevokeRequest) -> RevokePlan:
    """Quitar a una persona (correo) o grupo (`group-<id>`) de varias hojas.

    Sin `sheet_ids`, de todas. Por defecto sólo simula; propietario y heredados se omiten.
    """
    return await services.bulk.revoke(key, body)
