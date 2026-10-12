from datetime import datetime

from pydantic import BaseModel

from app.models.people import FailedSheet
from app.models.sheets import SheetSummary
from app.services.permissions import AccessLevel, ShareType


class AlertPerson(BaseModel):
    key: str
    type: ShareType
    name: str | None = None
    email: str | None = None
    access_level: AccessLevel


class AuditAlert(BaseModel):
    code: str
    severity: str
    message: str
    count: int
    people: list[AlertPerson]


class DomainCount(BaseModel):
    domain: str
    count: int
    is_personal: bool


class SheetAudit(BaseModel):
    sheet: SheetSummary
    total: int
    by_level: dict[str, int]
    by_scope: dict[str, int]
    by_domain: list[DomainCount]
    org_known: bool
    external_count: int | None = None
    unnamed_count: int
    not_in_contacts_count: int
    alerts: list[AuditAlert]


class ComparePerson(BaseModel):
    key: str
    type: ShareType
    name: str | None = None
    email: str | None = None
    level_a: AccessLevel | None = None
    level_b: AccessLevel | None = None


class SheetComparison(BaseModel):
    a: SheetSummary
    b: SheetSummary
    only_in_a: list[ComparePerson]
    only_in_b: list[ComparePerson]
    level_differences: list[ComparePerson]
    same_count: int


class SheetAccessRow(BaseModel):
    sheet_id: str
    sheet_name: str
    modified_at: datetime | None = None
    share_count: int
    editors_count: int
    external_count: int | None = None
    personal_email_count: int
    is_inactive: bool


class AccessSummary(BaseModel):
    sheets: list[SheetAccessRow]
    failed_sheets: list[FailedSheet]


class ReviewSheet(BaseModel):
    sheet_id: str
    sheet_name: str
    has_dynamic_view: bool
    max_severity: str
    alerts: dict[str, int]


class ReviewPerson(BaseModel):
    key: str
    type: ShareType
    name: str | None = None
    email: str | None = None
    codes: list[str]
    sheet_count: int


class ReviewTotals(BaseModel):
    sheets_reviewed: int
    sheets_with_alerts: int
    people_by_code: dict[str, int]


class AccountReview(BaseModel):
    min_severity: str
    totals: ReviewTotals
    sheets: list[ReviewSheet]
    people: list[ReviewPerson]
    failed_sheets: list[FailedSheet]
