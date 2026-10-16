from datetime import datetime

from pydantic import BaseModel

from app.models.sheets import SheetSummary
from app.services.permissions import AccessLevel


class Author(BaseModel):
    email: str | None = None
    name: str | None = None


class ChangedRow(BaseModel):
    row_id: str
    row_number: int | None = None
    label: str | None = None
    created_at: datetime | None = None
    created_by: Author | None = None
    modified_at: datetime | None = None
    modified_by: Author | None = None


class ActivityEditor(BaseModel):
    email: str | None = None
    name: str | None = None
    rows_changed: int
    last_change: datetime | None = None
    # Nivel actual en la hoja; None si ya no tiene la hoja compartida.
    access_level: AccessLevel | None = None


class IdleEditor(BaseModel):
    key: str
    email: str | None = None
    name: str | None = None
    access_level: AccessLevel


class SheetActivity(BaseModel):
    sheet: SheetSummary
    days: int
    since: datetime
    rows_total: int
    changed_rows_total: int
    changed_rows: list[ChangedRow]
    editors: list[ActivityEditor]
    idle_editors: list[IdleEditor]
    limitations: list[str]


class CellChange(BaseModel):
    column_id: str
    column_title: str
    value: str | None = None
    modified_at: datetime | None = None
    modified_by: Author | None = None


class RowHistory(BaseModel):
    sheet_id: str
    row_id: str
    changes: list[CellChange]
    columns_checked: int
    failed_columns: int
