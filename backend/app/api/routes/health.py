from fastapi import APIRouter

from app.api.deps import ServicesDep

router = APIRouter()


@router.get("/health")
async def health(services: ServicesDep) -> dict[str, str | bool]:
    """Estado del servicio sin llamar a Smartsheet."""
    settings = services.settings
    return {
        "status": "ok",
        "smartsheet": "configured" if settings.has_token else "missing_token",
        "read_only": settings.app_read_only,
    }

