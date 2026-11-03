"""Contrato de la revisión de proyectos y clientes, sin escrituras."""

from typing import Literal

from pydantic import BaseModel

from app.models.sheets import SheetSummary


class AssociationIssue(BaseModel):
    row_id: str
    row_number: int | None
    customer: str
    project: str
    reason: Literal["missing_customer", "unknown_project", "ambiguous_project", "wrong_customer"]


class AssociationReport(BaseModel):
    sheet: SheetSummary
    catalog_sheet: SheetSummary
    customer_column: str
    project_column: str
    catalog_customer_column: str
    catalog_project_column: str
    checked_rows: int
    issues_count: int
    issues: list[AssociationIssue]
    truncated: bool
