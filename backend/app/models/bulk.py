from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.people import Person
from app.models.sheets import SheetSummary
from app.services.bulk_plans import StepAction
from app.services.permissions import AccessLevel, ShareType

StepStatus = Literal["planned", "done", "failed", "not_applicable"]


class CopyRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_sheet_id": "5750050894335876",
                    "upgrade_levels": False,
                    "include_inherited": False,
                    "dry_run": True,
                }
            ]
        }
    )

    source_sheet_id: str = Field(pattern=r"^[A-Za-z0-9]{1,64}$")
    upgrade_levels: bool = False
    include_inherited: bool = False
    # Simulación por defecto: ejecutar exige pedirlo explícitamente (ADR-B13).
    dry_run: bool = True


class RevokeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"sheet_ids": None, "dry_run": True}]}
    )

    sheet_ids: list[str] | None = Field(default=None, max_length=500)
    dry_run: bool = True


class BulkStep(BaseModel):
    action: StepAction
    status: StepStatus
    key: str
    type: ShareType
    name: str | None = None
    email: str | None = None
    sheet_id: str
    sheet_name: str
    share_id: str | None = None
    current_level: AccessLevel | None = None
    new_level: AccessLevel | None = None
    reason: str | None = None
    error_code: str | None = None


class CopyPlan(BaseModel):
    source: SheetSummary
    target: SheetSummary
    dry_run: bool
    counts: dict[str, int]
    steps: list[BulkStep]


class RevokePlan(BaseModel):
    person: Person
    dry_run: bool
    counts: dict[str, int]
    steps: list[BulkStep]
