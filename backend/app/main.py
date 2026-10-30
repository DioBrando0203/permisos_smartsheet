"""Aplicación FastAPI: middlewares, errores, ciclo de vida del cliente y build del panel."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.deps import Services, build_services
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError, app_error_handler
from app.core.middleware import OriginMiddleware
from app.frontend import DEFAULT_DIST, mount_frontend


def create_app(
    settings: Settings | None = None,
    services: Services | None = None,
    frontend_dist: Path | None = DEFAULT_DIST,
) -> FastAPI:
    settings = settings or get_settings()
    services = services or build_services(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await services.client.aclose()
        await services.maps.aclose()

    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/docs", lifespan=lifespan)
    app.state.services = services
    app.add_exception_handler(AppError, app_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(OriginMiddleware, allowed_origins=settings.allowed_origins)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.allowed_hosts))
    app.include_router(api_router, prefix="/api")
    # Al final: la ruta comodín del panel no debe tapar a la API ni a /docs.
    mount_frontend(app, frontend_dist)
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# httpx registra en INFO la URL completa con su query (correos, búsquedas): sólo advertencias.
# El registro propio de `transport.py` ya deja método, ruta sin query, estado y duración.
logging.getLogger("httpx").setLevel(logging.WARNING)
app = create_app()
