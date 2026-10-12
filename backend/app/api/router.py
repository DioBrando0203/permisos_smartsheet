from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.people import router as people_router
from app.api.routes.sheets import router as sheets_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["estado"])
api_router.include_router(sheets_router, prefix="/sheets", tags=["hojas y permisos"])
api_router.include_router(people_router, tags=["personas"])
