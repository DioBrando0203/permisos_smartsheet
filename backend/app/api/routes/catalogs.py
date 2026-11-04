"""Catálogo de proyectos para Linked Tracking (SPEC-B16): consultas y sincronización protegida."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import ServicesDep
from app.api.routes.idsmart import require_admin
from app.core.errors import AppError
from app.services.catalog_rules import Origin, filter_catalog
from app.services.catalog_sync import sync_catalog
from app.services.project_catalog import (
    PROJECTS_SHEET,
    ProjectCatalogService,
    entry_json,
    sync_plan,
    validation_report,
)

router = APIRouter()
Code = Annotated[str | None, Query(pattern=r"^[A-Za-z0-9]{1,8}$", examples=["BS"])]


def _catalog(services: ServicesDep) -> ProjectCatalogService:
    return ProjectCatalogService(
        services.sheets, services.quality, services.settings.app_project_catalog_sheet
    )


@router.get("/catalogs/projects", summary="Proyectos de un cliente para Linked Tracking")
async def catalog_projects(
    services: ServicesDep,
    customer_code: Code = None,
    company: Code = None,
    include_historical: bool = True,
    refresh: bool = False,
) -> dict:
    """Actuales (con Stable ID) e históricos conocidos, agrupados por cliente."""
    snapshot = await _catalog(services).snapshot(refresh=refresh)
    entries = filter_catalog(snapshot.entries, customer_code, company)
    if not include_historical:
        entries = [entry for entry in entries if entry.origin == Origin.CURRENT]
    return {
        "customer_code": customer_code.upper() if customer_code else None,
        "company": company.upper() if company else None,
        "source_sheet": PROJECTS_SHEET,
        "catalog_sheet": _catalog(services).catalog_sheet or None,
        "projects": [entry_json(entry) for entry in entries],
        "duplicates": snapshot.duplicates,
    }


@router.get("/catalogs/linked-tracking", summary="Validar Linked Tracking contra el cliente")
async def linked_tracking_validation(
    services: ServicesDep, only_issues: bool = False, refresh: bool = False
) -> dict:
    report = validation_report(await _catalog(services).snapshot(refresh=refresh))
    if only_issues:
        report["items"] = [item for item in report["items"] if not item["valid"]]
    return report


@router.get("/catalogs/projects/sync-plan", summary="Simular la sincronización de la hoja catálogo")
async def catalog_sync_plan(services: ServicesDep, refresh: bool = False) -> dict:
    catalog = _catalog(services)
    changes = sync_plan(await catalog.snapshot(refresh=refresh))
    return {
        "dry_run": True,
        "catalog_sheet": catalog.catalog_sheet or None,
        "changes": [
            {"project_id": c.project_id, "action": c.action.value, "customer_code": c.customer}
            for c in changes
        ],
    }


@router.post(
    "/catalogs/projects/sync",
    summary="Sincronizar la hoja catálogo (Pruebas)",
    dependencies=[Depends(require_admin)],
)
async def catalog_sync(services: ServicesDep) -> dict:
    """Agrega proyectos nuevos y corrige el cliente; nunca borra filas ni toca el piloto."""
    try:
        counts = await sync_catalog(services.settings, services.client, _catalog(services))
    except ValueError as error:
        raise AppError("CATALOG_SYNC_BLOCKED", str(error), 403) from None
    return {"dry_run": False, "counts": counts}
