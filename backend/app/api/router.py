from fastapi import APIRouter

from app.api.routes.catalogs import router as catalogs_router
from app.api.routes.health import router as health_router
from app.api.routes.idsmart import router as idsmart_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["estado"])
api_router.include_router(idsmart_router, prefix="/ids", tags=["Galp - ID Manager"])
api_router.include_router(catalogs_router, tags=["Galp - Catálogo de proyectos"])
