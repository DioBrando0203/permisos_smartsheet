from pydantic import BaseModel

from app.models.people import FailedSheet
from app.services.permissions import AccessLevel


class DesignerPerson(BaseModel):
    key: str
    email: str | None = None
    name: str | None = None


class DesignerSheet(BaseModel):
    sheet_id: str
    sheet_name: str
    open: int
    on_hold: int
    closed: int
    # None: no se pudo identificar a la persona en el directorio.
    has_access: bool | None = None
    access_level: AccessLevel | None = None


class DesignerLoad(BaseModel):
    name: str
    in_catalog: bool | None = None
    person: DesignerPerson | None = None
    ambiguous: bool
    open: int
    on_hold: int
    closed: int
    by_phase: dict[str, int]
    sheets_without_access: int
    sheets: list[DesignerSheet]


class SheetGap(BaseModel):
    sheet_id: str
    sheet_name: str
    open_without_designer: int
    without_status: int


class DesignerWorkload(BaseModel):
    designer_columns: list[str]
    status_column: str
    closed_statuses: list[str]
    sheets_reviewed: int
    sheets_with_designers: int
    open_total: int
    on_hold_total: int
    closed_total: int
    header_like_rows: int
    designers: list[DesignerLoad]
    sheet_gaps: list[SheetGap]
    failed_sheets: list[FailedSheet]
