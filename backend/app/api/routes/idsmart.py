"""ID Manager autenticado: consultas, simulación y escrituras sólo con todas las barreras."""

import asyncio
import secrets
from typing import Annotated, Literal

import psycopg
from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.api.deps import ServicesDep
from app.core.errors import AppError
from app.services.ids import manual
from app.services.ids.cli import DSN
from app.services.ids.database import (
    assignments,
    audit_events,
    database_summary,
    pending_reservations,
)
from app.services.ids.preview import build_dry_run_report
from app.services.ids.recovery import plan_recovery
from app.services.ids.runtime import write_barriers, writes_allowed

security = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
_DB_ERROR = ("IDS_DATABASE_UNAVAILABLE", "No se pudo consultar PostgreSQL.", 503)
_INVENTORY_ERROR = ("IDS_INVENTORY_CONFLICT", "No se pudo validar el inventario del piloto.", 409)


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


class AssignRow(BaseModel):
    sheet_id: int = Field(gt=0)
    row_id: int = Field(gt=0)
    parent: str = Field(min_length=1, max_length=64, description="Ámbito o ID del padre")
    authorize_test_write: bool = False


@router.get("/status", summary="Consultar estado del ID Manager")
async def get_ids_status(request: Request, services: ServicesDep) -> dict:
    monitor = request.app.state.ids_monitor
    settings = services.settings
    return {
        "service": "GALP ID Manager",
        "read_only": settings.app_read_only,
        "automatic_generation_enabled": monitor.enabled and monitor.mode == "assign",
        "smartsheet_writes_enabled": writes_allowed(settings),
        "write_barriers": write_barriers(settings)
        | {"ids_processor_writes_enabled": settings.ids_processor_writes_enabled},
        "processor_enabled": monitor.enabled,
        "processor_mode": monitor.mode,
        "processor_active": monitor.active,
        "processor_interval_seconds": monitor.interval,
        "processor_poll_seconds": monitor.poll_seconds,
        "processor_max_rows": monitor.max_rows,
        "last_run": monitor.last_run,
        "last_error": monitor.last_error,
        "last_counts": monitor.last_counts,
        "last_outcomes": monitor.last_outcomes,
        "last_catalog_sync": monitor.last_catalog,
    }


@router.get("/database", summary="Conteos de PostgreSQL")
async def get_ids_database() -> dict:
    return await asyncio.to_thread(database_summary)


@router.get("/assignments", summary="Asignaciones registradas")
async def get_ids_assignments(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sheet_id: Annotated[int | None, Query(gt=0)] = None,
    kind: Literal["project", "task", "record", "revision"] | None = None,
    state: Literal["reservado", "confirmado"] | None = None,
) -> dict:
    return await asyncio.to_thread(assignments, limit, offset, sheet_id, kind, state)


@router.get("/audit", summary="Eventos de auditoría, más recientes primero")
async def get_ids_audit(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    action: Literal["inicializado", "reservado", "confirmado"] | None = None,
) -> dict:
    return await asyncio.to_thread(audit_events, limit, offset, action)


async def _report(services: ServicesDep) -> dict:
    try:
        return await build_dry_run_report(services.client, DSN)
    except psycopg.Error:
        raise AppError(*_DB_ERROR) from None
    except ValueError:
        raise AppError(*_INVENTORY_ERROR) from None


@router.get("/dry-run", summary="Simular sin reservar ni escribir")
async def get_ids_dry_run(services: ServicesDep) -> dict:
    return await _report(services)


@router.get("/conflicts", summary="Conflictos actuales y del último ciclo")
async def get_ids_conflicts(request: Request, services: ServicesDep) -> dict:
    report = await _report(services)
    monitor = request.app.state.ids_monitor
    return {
        "source": "current_dry_run",
        "processor_error": monitor.last_error,
        "conflicts": [
            row for row in report["pending_or_conflicting_rows"] if row["action"] == "conflict"
        ],
        "last_cycle_conflicts": [
            row for row in monitor.last_results if row["outcome"] in ("conflict", "denied")
        ],
    }


@router.get("/recovery", summary="Operaciones incompletas y cómo se retoman")
async def get_ids_recovery(services: ServicesDep) -> dict:
    report = await _report(services)
    reserved = await asyncio.to_thread(pending_reservations)
    return {"read_only_check": True, "pending": plan_recovery(reserved, report)}


@router.post("/rows/assign", summary="Asignar el Stable ID de una fila designada")
async def assign_ids_row(body: AssignRow, services: ServicesDep) -> dict:
    """Prueba controlada de una sola fila; exige las tres barreras y autorización expresa."""
    target = (body.sheet_id, body.row_id, body.parent)
    try:
        return await manual.assign_row(
            services.settings, services.client, DSN, target, body.authorize_test_write
        )
    except psycopg.Error:
        raise AppError(*_DB_ERROR) from None
    except ValueError as error:
        # Mensajes propios del ID Manager: no contienen datos de celdas ni credenciales.
        raise AppError("IDS_ASSIGN_BLOCKED", str(error), 403) from None


@router.post("/processor/run", summary="Ejecutar ahora un ciclo del procesador")
async def run_ids_processor(request: Request) -> dict:
    """Simula salvo que el procesador tenga escritura habilitada; nunca se solapa."""
    try:
        return await request.app.state.ids_monitor.run_once()
    except psycopg.Error:
        raise AppError(*_DB_ERROR) from None
    except ValueError:
        raise AppError(*_INVENTORY_ERROR) from None


@router.get("/health", summary="Conexión con PostgreSQL y Smartsheet")
async def get_ids_health(services: ServicesDep) -> dict:
    await asyncio.to_thread(database_summary)
    await services.client.get_me()
    return {"postgresql": "ok", "smartsheet": "ok", "read_only": services.settings.app_read_only}
