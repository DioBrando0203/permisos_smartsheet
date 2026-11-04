"""Sincroniza la hoja catálogo en Pruebas desde Proyectos: agrega o actualiza, nunca borra."""

from collections.abc import Awaitable, Callable

from app.core.config import Settings
from app.services.catalog_plan import CatalogAction
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.pilot import SHEETS
from app.services.ids.runtime import writes_allowed
from app.services.project_catalog import (
    CATALOG_COLUMNS,
    ORIGIN_LABELS,
    CatalogSnapshot,
    ProjectCatalogService,
    sync_plan,
)
from app.services.quality import QualityService
from app.services.sheets import SheetService
from app.services.smartsheet import SmartsheetClient


async def check_catalog_target(settings: Settings, client: SmartsheetClient, sheet: str) -> None:
    """Barreras: escritura aprobada, hoja configurada, distinta del piloto y dentro de Pruebas."""
    if not writes_allowed(settings):
        raise ValueError("Escritura deshabilitada por las barreras del servicio")
    if not sheet.isdigit() or sheet in {item[0] for item in SHEETS}:
        raise ValueError("Hoja catálogo no configurada o reservada para el piloto")
    if await client.sheet_workspace_id(sheet) != PILOT_WORKSPACE:
        raise ValueError("La hoja catálogo no pertenece al workspace Pruebas")


def _cells(snapshot: CatalogSnapshot, value: str) -> list[dict]:
    entry = next(item for item in snapshot.entries if item.tracking_project == value)
    values = (
        entry.tracking_project,
        entry.customer_code,
        entry.customer,
        entry.company,
        ORIGIN_LABELS[entry.origin],
    )
    return [
        {"columnId": int(snapshot.catalog_columns[name]), "value": cell}
        for name, cell in zip(CATALOG_COLUMNS, values, strict=True)
    ]


async def sync_catalog(
    settings: Settings, client: SmartsheetClient, catalog: ProjectCatalogService
) -> dict:
    """Aplica el plan: filas nuevas al final y cambio de cliente; conflictos sólo se informan."""
    await check_catalog_target(settings, client, catalog.catalog_sheet)
    snapshot = await catalog.snapshot(refresh=True)
    changes = sync_plan(snapshot)
    rows = {entry.tracking_project.casefold(): row_id for row_id, entry in snapshot.destination}
    add = [
        {"toBottom": True, "cells": _cells(snapshot, change.project_id)}
        for change in changes
        if change.action == CatalogAction.ADD
    ]
    update = [
        {
            "id": int(rows[change.project_id.casefold()]),
            "cells": _cells(snapshot, change.project_id)[1:3],
        }
        for change in changes
        if change.action == CatalogAction.UPDATE
    ]
    await client.upsert_catalog_rows(catalog.catalog_sheet, add, update)
    if add or update:
        # El desplegable vinculado muestra el orden de la hoja: agrupar por cliente y empresa.
        order = [snapshot.catalog_columns[name] for name in ("Customer Code", "Company")]
        order.append(snapshot.catalog_columns["Tracking Project"])
        await client.sort_catalog_rows(catalog.catalog_sheet, order)
    counts = {action.value: 0 for action in CatalogAction}
    for change in changes:
        counts[change.action.value] += 1
    return counts


def catalog_hook(
    settings: Settings, client: SmartsheetClient, sheets: SheetService, quality: QualityService
) -> Callable[[], Awaitable[dict]] | None:
    """Sincronización tras cada ciclo de asignación; None si no hay catálogo o escritura."""
    if not settings.app_project_catalog_sheet.strip() or not writes_allowed(settings):
        return None
    catalog = ProjectCatalogService(sheets, quality, settings.app_project_catalog_sheet)
    return lambda: sync_catalog(settings, client, catalog)
