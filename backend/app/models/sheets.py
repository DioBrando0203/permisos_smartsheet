from datetime import datetime

from pydantic import BaseModel

from app.services.permissions import AccessLevel


class SheetSummary(BaseModel):
    id: str
    name: str
    access_level: AccessLevel
    can_manage_shares: bool
    permalink: str | None = None
    modified_at: datetime | None = None


class SheetList(BaseModel):
    sheets: list[SheetSummary]
    total: int
    loaded_at: datetime | None = None
