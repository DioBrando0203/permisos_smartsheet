from fastapi import APIRouter

from app.api.routes.activity import router as activity_router
from app.api.routes.automations import router as automations_router
from app.api.routes.bulk import router as bulk_router
from app.api.routes.export import router as export_router
from app.api.routes.health import router as health_router
from app.api.routes.people import router as people_router
from app.api.routes.quality import router as quality_router
from app.api.routes.references import router as references_router
from app.api.routes.reports import router as reports_router
from app.api.routes.sheets import router as sheets_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["estado"])
# Reportes antes que hojas: "/sheets/compare" no debe tomarse como un código de permalink.
api_router.include_router(reports_router, prefix="/sheets", tags=["auditoría y comparación"])
api_router.include_router(sheets_router, prefix="/sheets", tags=["hojas y permisos"])
api_router.include_router(
    activity_router, prefix="/sheets", tags=["actividad (directo de Smartsheet)"]
)
api_router.include_router(bulk_router, tags=["operaciones masivas (simulación por defecto)"])
api_router.include_router(people_router, tags=["personas"])
api_router.include_router(quality_router, prefix="/sheets", tags=["calidad de datos"])
api_router.include_router(export_router, tags=["exportar"])
api_router.include_router(automations_router, tags=["automatizaciones de Smartsheet"])
api_router.include_router(references_router, tags=["calidad de datos"])
