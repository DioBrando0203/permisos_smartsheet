"""Catálogo de proyectos del piloto para Linked Tracking: lecturas con caché, sin escrituras."""

from collections import Counter
from dataclasses import asdict, dataclass

from app.services.catalog_plan import CatalogChange, Project, plan_catalog
from app.services.catalog_rules import (
    VALID,
    CatalogEntry,
    Origin,
    ProjectRow,
    build_catalog,
    classify_link,
    id_parts,
)
from app.services.ids import pilot
from app.services.quality import QualityService, find_column
from app.services.sheets import SheetService

# En este orden se arma `ProjectRow`; la empresa es opcional (sin ella, la de la fórmula).
SOURCE_COLUMNS = (
    "Stable Tracking Project",
    "Tracking Project",
    "Customer",
    "Customer Code",
    "KMV/GALP",
    "Linked Tracking",
)
COMPANY_INDEX = 4
# Columnas de la hoja catálogo (Pruebas); la primera es el valor del desplegable vinculado.
CATALOG_COLUMNS = ("Tracking Project", "Customer Code", "Customer", "Company", "Origin")
ORIGIN_LABELS = {Origin.CURRENT: "Actual", Origin.HISTORICAL: "Histórico"}


@dataclass(frozen=True)
class CatalogSnapshot:
    rows: list[ProjectRow]
    entries: list[CatalogEntry]
    duplicates: list[str]
    # Filas existentes de la hoja catálogo: (id de fila, entrada), y columnas por título.
    destination: list[tuple[str, CatalogEntry]]
    catalog_columns: dict[str, str]


class ProjectCatalogService:
    def __init__(self, sheets: SheetService, quality: QualityService, catalog_sheet: str) -> None:
        self._sheets = sheets
        self._quality = quality
        self.catalog_sheet = catalog_sheet.strip()

    async def snapshot(self, *, refresh: bool) -> CatalogSnapshot:
        rows, customers = await self._source(refresh)
        destination, columns = await self._destination(refresh)
        # Históricos sólo desde la hoja catálogo: el desplegable vinculado ya es su copia.
        known = [
            entry.tracking_project for _, entry in destination if entry.origin == Origin.HISTORICAL
        ]
        entries, duplicates = build_catalog(rows, known, customers)
        return CatalogSnapshot(rows, entries, duplicates, destination, columns)

    async def _source(self, refresh: bool) -> tuple[list[ProjectRow], tuple]:
        sheet = pilot.project_sheet()
        columns = await self._sheets.columns(sheet)
        titles = {column.title for column in columns}
        found = [
            find_column(name, columns) if name in titles or i != COMPANY_INDEX else None
            for i, name in enumerate(SOURCE_COLUMNS)
        ]
        ids = [column.id if column else None for column in found]
        raw = await self._quality.rows(sheet, [i for i in ids if i], refresh=refresh)
        rows = [
            ProjectRow(
                row.id,
                row.row_number,
                *((row.cells.get(i) or "").strip() if i else pilot.DEFAULT_COMPANY for i in ids),
            )
            # Sólo filas madre: las hijas repiten el ID de su proyecto.
            for row in raw
            if not row.parent_id
        ]
        return rows, found[2].options

    async def _destination(self, refresh: bool) -> tuple[list[tuple[str, CatalogEntry]], dict]:
        if not self.catalog_sheet:
            return [], {}
        columns = await self._sheets.columns(self.catalog_sheet)
        found = {name: find_column(name, columns).id for name in CATALOG_COLUMNS}
        raw = await self._quality.rows(self.catalog_sheet, list(found.values()), refresh=refresh)
        result = []
        for row in raw:
            value, code, customer, company, origin = (
                (row.cells.get(found[name]) or "").strip() for name in CATALOG_COLUMNS
            )
            if value:
                kind = (
                    Origin.HISTORICAL
                    if origin == ORIGIN_LABELS[Origin.HISTORICAL]
                    else (Origin.CURRENT)
                )
                result.append((row.id, CatalogEntry(value, company, code, customer, kind)))
        return result, found


def validation_report(snapshot: CatalogSnapshot) -> dict:
    """Clasifica cada Linked Tracking; informa sin modificar ninguna asociación."""
    catalog = {entry.tracking_project: entry for entry in snapshot.entries}
    items = []
    for row in snapshot.rows:
        if not (row.stable or row.visible or row.linked):
            continue
        status = classify_link(row, catalog)
        company = row.company
        try:
            linked_company = id_parts(row.linked)[0] if row.linked else ""
        except ValueError:
            linked_company = ""
        items.append(
            {
                "row_id": row.row_id,
                "row_number": row.row_number,
                "tracking_project": row.stable or row.visible,
                "customer_code": row.customer_code,
                "company": company,
                "linked_tracking": row.linked,
                "status": status.value,
                "valid": status in VALID,
                "same_company": not linked_company or linked_company == company,
            }
        )
    return {
        "counts": dict(Counter(item["status"] for item in items)),
        "items": items,
        "duplicates": snapshot.duplicates,
        "note": "Sólo lectura: ninguna referencia se corrige ni se borra automáticamente.",
    }


def sync_plan(snapshot: CatalogSnapshot) -> list[CatalogChange]:
    """Qué agregar o actualizar en la hoja catálogo; nunca propone borrados (históricos)."""
    source = [Project(entry.tracking_project, entry.customer_code) for entry in snapshot.entries]
    destination = [
        Project(entry.tracking_project, entry.customer_code) for _, entry in snapshot.destination
    ]
    return plan_catalog(source, destination)


def entry_json(entry: CatalogEntry) -> dict:
    return asdict(entry) | {"origin": entry.origin.value}
