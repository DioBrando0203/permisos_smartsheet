"""Consulta de asociaciones entre una hoja y un catálogo, sin escrituras."""

from dataclasses import dataclass

from app.models.associations import AssociationReport
from app.services.association_rules import validate_associations
from app.services.quality import QualityService, find_column
from app.services.quality_rules import MAX_ISSUES
from app.services.sheets import SheetService
from app.services.smartsheet import RawColumn, RawRow


@dataclass(frozen=True)
class AssociationRequest:
    customer_column: str
    project_column: str
    catalog_sheet: str
    catalog_customer_column: str
    catalog_project_column: str


class AssociationService:
    def __init__(self, sheets: SheetService, quality: QualityService) -> None:
        self._sheets = sheets
        self._quality = quality

    async def check(
        self, sheet_id: str, request: AssociationRequest, *, refresh: bool
    ) -> AssociationReport:
        sheet = await self._sheets.get(sheet_id)
        catalog_id = await self._sheets.resolve_id(request.catalog_sheet)
        catalog_sheet = await self._sheets.get(catalog_id)
        customer, project, rows = await self._read(
            sheet_id, request.customer_column, request.project_column, refresh
        )
        catalog_customer, catalog_project, catalog = await self._read(
            catalog_id, request.catalog_customer_column, request.catalog_project_column, refresh
        )
        issues = validate_associations(
            rows, catalog, (customer.id, project.id, catalog_customer.id, catalog_project.id)
        )
        return AssociationReport(
            sheet=sheet,
            catalog_sheet=catalog_sheet,
            customer_column=customer.title,
            project_column=project.title,
            catalog_customer_column=catalog_customer.title,
            catalog_project_column=catalog_project.title,
            checked_rows=sum(bool((row.cells.get(project.id) or "").strip()) for row in rows),
            issues_count=len(issues),
            issues=issues[:MAX_ISSUES],
            truncated=len(issues) > MAX_ISSUES,
        )

    async def _read(
        self, sheet_id: str, customer: str, project: str, refresh: bool
    ) -> tuple[RawColumn, RawColumn, list[RawRow]]:
        columns = await self._sheets.columns(sheet_id)
        customer_col = find_column(customer, columns)
        project_col = find_column(project, columns)
        label = next((column for column in columns if column.primary), columns[0])
        wanted = list(dict.fromkeys((label.id, customer_col.id, project_col.id)))
        return (
            customer_col,
            project_col,
            await self._quality.rows(sheet_id, wanted, refresh=refresh),
        )
