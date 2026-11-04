"""Consultas autenticadas del ID Manager; ninguna operación escribe en Smartsheet."""

import asyncio
import secrets
from typing import Annotated, Literal

import psycopg
from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import ServicesDep
from app.core.errors import AppError
from app.services.ids.cli import DSN
from app.services.ids.database import assignments, database_summary
from app.services.ids.preview import build_dry_run_report

security = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(security)]


async def require_admin(request: Request, credentials: Credentials) -> None:
    """Comprueba token administrativo separado del token de Smartsheet."""
    token = request.app.state.services.settings.ids_admin_token
    if token is None or not token.get_secret_value().strip():
        raise AppError("IDS_AUTH_NOT_CONFIGURED", "Autenticación de IDs no configurada.", 503)
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), token.get_secret_value().encode()
    ):
        raise AppError("IDS_UNAUTHORIZED", "Credenciales de IDs inválidas.", 401)


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/status", summary="Consultar estado del ID Manager")
async def get_ids_status(request: Request, services: ServicesDep) -> dict:
    monitor = request.app.state.ids_monitor
    return {
        "service": "GALP ID Manager",
        "read_only": services.settings.app_read_only,
        "automatic_generation_enabled": False,
        "smartsheet_writes_enabled": (
            not services.settings.app_read_only
            and services.settings.ids_writes_enabled
            and services.settings.ids_transition_approved
        ),
        "processor_enabled": monitor.enabled,
        "processor_active": monitor.active,
        "last_run": monitor.last_run,
        "last_error": monitor.last_error,
        "last_counts": monitor.last_counts,
    }


@router.get("/database")
async def get_ids_database() -> dict:
    return await asyncio.to_thread(database_summary)


@router.get("/assignments")
async def get_ids_assignments(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sheet_id: Annotated[int | None, Query(gt=0)] = None,
    kind: Literal["project", "task", "record", "revision"] | None = None,
    state: Literal["reservado", "confirmado"] | None = None,
) -> dict:
    return await asyncio.to_thread(assignments, limit, offset, sheet_id, kind, state)


async def _report(services: ServicesDep) -> dict:
    try:
        return await build_dry_run_report(services.client, DSN)
    except psycopg.Error:
        raise AppError(
            "IDS_DATABASE_UNAVAILABLE", "No se pudo consultar PostgreSQL.", 503
        ) from None
    except ValueError:
        raise AppError(
            "IDS_INVENTORY_CONFLICT", "No se pudo validar el inventario del piloto.", 409
        ) from None


@router.get("/dry-run")
async def get_ids_dry_run(services: ServicesDep) -> dict:
    return await _report(services)


@router.get("/conflicts")
async def get_ids_conflicts(request: Request, services: ServicesDep) -> dict:
    report = await _report(services)
    return {
        "source": "current_dry_run",
        "processor_error": request.app.state.ids_monitor.last_error,
        "conflicts": [
            row for row in report["pending_or_conflicting_rows"] if row["action"] == "conflict"
        ],
    }


@router.get("/health")
async def get_ids_health(services: ServicesDep) -> dict:
    await asyncio.to_thread(database_summary)
    await services.client.get_me()
    return {"postgresql": "ok", "smartsheet": "ok", "read_only": services.settings.app_read_only}
