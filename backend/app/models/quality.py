from typing import Literal

from pydantic import BaseModel

from app.models.people import FailedSheet
from app.models.sheets import SheetSummary


class ColumnInfo(BaseModel):
    id: str
    title: str
    type: str | None = None
    index: int
    primary: bool


class QualityRow(BaseModel):
    row_id: str
    row_number: int | None = None
    label: str | None = None


class QualityIssue(BaseModel):
    # Valor repetido o que no cumple el formato; None para celdas vacías.
    value: str | None = None
    rows: list[QualityRow]


class QualityCheck(BaseModel):
    column: str
    column_id: str
    check: Literal["unique", "required", "pattern"]
    pattern: str | None = None
    issues_count: int
    issues: list[QualityIssue]
    truncated: bool


class SheetQuality(BaseModel):
    sheet: SheetSummary
    rows_total: int
    checks: list[QualityCheck]


class SheetReferences(BaseModel):
    sheet: SheetSummary
    column: str
    catalog_sheet: SheetSummary
    catalog_column: str
    catalog_values_count: int
    checked_rows: int
    missing_count: int
    missing: list[QualityIssue]
    truncated: bool


class ReferenceSheetRow(BaseModel):
    sheet_id: str
    sheet_name: str
    missing_count: int
    missing_values: list[str]


class MissingValue(BaseModel):
    value: str
    sheets: int
    rows: int


class AccountReferences(BaseModel):
    column: str
    catalog_sheet: SheetSummary
    catalog_column: str
    catalog_values_count: int
    sheets_checked: int
    sheets_without_column: int
    missing_total: int
    by_value: list[MissingValue]
    sheets: list[ReferenceSheetRow]
    failed_sheets: list[FailedSheet]
