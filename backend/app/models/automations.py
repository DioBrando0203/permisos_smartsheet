from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.activity import Author
from app.models.people import FailedSheet
from app.models.sheets import SheetSummary

AutomationStatus = Literal["ok", "with_problems", "disabled"]


class RecipientColumn(BaseModel):
    id: str
    title: str | None = None
    type: str | None = None
    is_contact: bool
    exists: bool


class AutomationProblem(BaseModel):
    code: str
    message: str


class Automation(BaseModel):
    id: str
    name: str
    enabled: bool
    status: AutomationStatus
    action_type: str | None = None
    frequency: str | None = None
    recipient_emails: list[str]
    recipient_columns: list[RecipientColumn]
    notify_all_shared: bool
    smartsheet_reason: str | None = None
    problems: list[AutomationProblem]
    modified_at: datetime | None = None
    modified_by: Author | None = None


class SheetAutomations(BaseModel):
    sheet: SheetSummary
    counts: dict[str, int]
    automations: list[Automation]


class AutomationSheetRow(BaseModel):
    sheet_id: str
    sheet_name: str
    counts: dict[str, int]
    problems: dict[str, int]


class AccountAutomations(BaseModel):
    sheets_reviewed: int
    sheets_with_rules: int
    rules_total: int
    by_status: dict[str, int]
    by_problem: dict[str, int]
    sheets: list[AutomationSheetRow]
    failed_sheets: list[FailedSheet]
