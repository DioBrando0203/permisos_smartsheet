"""Referencias entre hojas (SPEC-B11): valores de una columna que no están en un catálogo.

Sólo lectura. Reutiliza la lectura de filas y la búsqueda de columnas de la calidad de datos.
"""

import asyncio
from collections import Counter
from dataclasses import dataclass

from app.core.errors import AppError
from app.models.people import FailedSheet
from app.models.quality import (
    AccountReferences,
    MissingValue,
    QualityIssue,
    ReferenceSheetRow,
    SheetReferences,
)
from app.services import quality_rules
from app.services.quality import QualityService, find_column, limit_issues
from app.services.search import matches
from app.services.sheets import SheetService
from app.services.smartsheet import RawColumn, RawRow, RawSheet


@dataclass(frozen=True)
class Catalog:
    sheet_id: str
    column: RawColumn
    values: set[str]


class ReferenceService:
    def __init__(self, sheets: SheetService, quality: QualityService) -> None:
        self._sheets = sheets
        self._quality = quality

    async def sheet(
        self,
        sheet_id: str,
        column: str,
        catalog_sheet: str,
        catalog_column: str,
        *,
        refresh: bool = False,
    ) -> SheetReferences:
        sheet = await self._sheets.get(sheet_id)
        catalog = await self.catalog(catalog_sheet, catalog_column, refresh=refresh)
        target, rows = await self._column_rows(sheet_id, column, refresh=refresh)
        issues = quality_rules.missing_references(rows, target.id, catalog.values)
        shown, truncated = limit_issues(issues)
        return SheetReferences(
            sheet=sheet,
            column=target.title,
            catalog_sheet=await self._sheets.get(catalog.sheet_id),
            catalog_column=catalog.column.title,
            catalog_values_count=len(catalog.values),
            checked_rows=sum(1 for row in rows if (row.cells.get(target.id) or "").strip()),
            missing_count=quality_rules.issue_count(issues),
            missing=shown,
            truncated=truncated,
        )

    async def account(
        self,
        column: str,
        catalog_sheet: str,
        catalog_column: str,
        query: str | None,
        *,
        refresh: bool = False,
    ) -> AccountReferences:
        catalog = await self.catalog(catalog_sheet, catalog_column, refresh=refresh)
        sheets = [
            sheet
            for sheet in await self._sheets.raw_sheets(refresh=refresh)
            if sheet.in_my_list and sheet.id != catalog.sheet_id and matches(query, sheet.name)
        ]
        results = await asyncio.gather(
            *(self._sheet_row(sheet, column, catalog, refresh) for sheet in sheets)
        )
        rows = [item for item in results if isinstance(item, tuple)]
        failed = [item for item in results if isinstance(item, FailedSheet)]
        checked = [row for row, _ in rows]
        counts = _by_value([issues for _, issues in rows])
        return AccountReferences(
            column=column,
            catalog_sheet=await self._sheets.get(catalog.sheet_id),
            catalog_column=catalog.column.title,
            catalog_values_count=len(catalog.values),
            sheets_checked=len(checked),
            sheets_without_column=sum(1 for item in results if item is None),
            missing_total=sum(row.missing_count for row in checked),
            by_value=counts,
            sheets=sorted(
                (row for row in checked if row.missing_count),
                key=lambda row: (-row.missing_count, row.sheet_name.casefold()),
            ),
            failed_sheets=failed,
        )

    async def catalog(self, sheet_ref: str, column: str, *, refresh: bool = False) -> Catalog:
        """Valores válidos de la columna de una hoja catálogo, normalizados."""
        sheet_id = await self._sheets.resolve_id(sheet_ref)
        target, rows = await self._column_rows(sheet_id, column, refresh=refresh)
        return Catalog(sheet_id, target, quality_rules.normalized_values(rows, target.id))

    async def _column_rows(
        self, sheet_id: str, column: str, *, refresh: bool
    ) -> tuple[RawColumn, list[RawRow]]:
        columns = await self._sheets.columns(sheet_id)
        target = find_column(column, columns)
        label = next((c for c in columns if c.primary), columns[0])
        wanted = [label.id] if label.id == target.id else [label.id, target.id]
        return target, await self._quality.rows(sheet_id, wanted, refresh=refresh)

    async def _sheet_row(
        self, sheet: RawSheet, column: str, catalog: Catalog, refresh: bool
    ) -> tuple[ReferenceSheetRow, list[QualityIssue]] | FailedSheet | None:
        """Faltantes de una hoja; `None` si no tiene la columna (Bulkhead para los fallos)."""
        try:
            target, rows = await self._column_rows(sheet.id, column, refresh=refresh)
        except AppError as error:
            if error.code == "COLUMN_NOT_FOUND":
                return None
            return FailedSheet(sheet_id=sheet.id, sheet_name=sheet.name, code=error.code)
        issues = quality_rules.missing_references(rows, target.id, catalog.values)
        row = ReferenceSheetRow(
            sheet_id=sheet.id,
            sheet_name=sheet.name,
            missing_count=quality_rules.issue_count(issues),
            missing_values=[issue.value or "" for issue in issues],
        )
        return row, issues


def _by_value(per_sheet: list[list[QualityIssue]]) -> list[MissingValue]:
    """Qué valor falta en más hojas: el primero que conviene corregir o agregar al catálogo."""
    sheets: Counter[str] = Counter()
    rows: Counter[str] = Counter()
    shown: dict[str, str] = {}
    for issues in per_sheet:
        for issue in issues:
            # Mismo criterio que dentro de una hoja: "PEPE" y "Pepe" son el mismo valor.
            key = (issue.value or "").casefold()
            shown.setdefault(key, issue.value or "")
            sheets[key] += 1
            rows[key] += len(issue.rows)
    values = [MissingValue(value=shown[k], sheets=sheets[k], rows=rows[k]) for k in sheets]
    return sorted(values, key=lambda item: (-item.sheets, -item.rows, item.value))
