from fastapi import APIRouter

from app.api.routes.bulk import router as bulk_router
from app.api.routes.health import router as health_router
from app.api.routes.people import router as people_router
from app.api.routes.reports import router as reports_router
from app.api.routes.sheets import router as sheets_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["estado"])
# Reportes antes que hojas: "/sheets/compare" no debe tomarse como un código de permalink.
api_router.include_router(reports_router, prefix="/sheets", tags=["auditoría y comparación"])
api_router.include_router(sheets_router, prefix="/sheets", tags=["hojas y permisos"])
api_router.include_router(bulk_router, tags=["operaciones masivas (simulación por defecto)"])
api_router.include_router(people_router, tags=["personas"])
