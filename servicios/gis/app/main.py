"""API GIS independiente del panel de Smartsheet."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import Settings
from app.core.errors import AppError, app_error_handler
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.map import MapService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    maps = MapService(settings, GisClient(settings), TtlCache(settings.gis_cache_ttl_seconds))

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await maps.aclose()

    app = FastAPI(title="GIS", lifespan=lifespan)
    app.state.maps = maps
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(router, prefix="/api/map", tags=["mapa"])
    return app


app = create_app()
