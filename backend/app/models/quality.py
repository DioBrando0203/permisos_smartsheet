from typing import Literal

from pydantic import BaseModel

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
