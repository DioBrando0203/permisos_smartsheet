"""Aplicación FastAPI del procesador y catálogo de Smartsheet."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.deps import Services, build_services
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError, app_error_handler
from app.core.logbook import install_logbook
from app.core.middleware import OriginMiddleware
from app.services.catalog_sync import catalog_hook
from app.services.childsheets.sync import child_hooks
from app.services.ids.monitor import IdlePolling, IdMonitor
from app.services.ids.runtime import assign_factory
from app.services.obs.sync import obs_hook
from app.services.step_gate import VersionBoard


def create_app(
    settings: Settings | None = None,
    services: Services | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    services = services or build_services(settings)
    logbook = install_logbook(settings.app_log_buffer_size)
    # Una lectura de versión por hoja y pasada, compartida por los pasos (SPEC-B21 CA-03).
    board = VersionBoard(services.client)
    idle = IdlePolling(
        settings.ids_monitor_idle_after_seconds, settings.ids_monitor_idle_poll_seconds
    )
    # Sin todas las barreras de escritura el procesador sólo simula (SPEC-ID01 ID-26).
    monitor = IdMonitor(
        services.client,
        settings.ids_monitor_enabled,
        settings.ids_monitor_interval_seconds,
        connector_factory=assign_factory(settings, services.client),
        max_rows=settings.ids_processor_max_rows,
        after_cycle=catalog_hook(settings, services.client, services.sheets, services.quality),
        poll_seconds=max(2, settings.ids_monitor_poll_seconds)
        if settings.ids_monitor_poll_seconds
        else None,
        obs_sync=obs_hook(settings, services.client, board=board),
        customer_change=settings.ids_customer_change_enabled,
        child_syncs=child_hooks(settings, services.client, board),
        idle=idle,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        monitor.start()
        yield
        await monitor.stop()
        await services.client.aclose()

    app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/docs", lifespan=lifespan)
    app.state.services = services
    app.state.ids_monitor = monitor
    app.state.logbook = logbook
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
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# httpx registra en INFO la URL completa con su query (correos, búsquedas): sólo advertencias.
# El registro propio de `transport.py` ya deja método, ruta sin query, estado y duración.
logging.getLogger("httpx").setLevel(logging.WARNING)
app = create_app()
