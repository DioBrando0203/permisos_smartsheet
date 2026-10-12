import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.permissions import AccessLevel, LockedReason, ShareScope, ShareType

_EMAIL = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")
_DIGITS = re.compile(r"^\d{1,20}$")


class Share(BaseModel):
    id: str
    type: ShareType
    user_id: str | None = None
    group_id: str | None = None
    email: str | None = None
    name: str | None = None
    access_level: AccessLevel
    scope: ShareScope
    editable: bool
    locked_reason: LockedReason | None = None


class ShareList(BaseModel):
    sheet_id: str
    shares: list[Share]
    loaded_at: datetime | None = None


class Recipient(BaseModel):
    email: str | None = None
    group_id: str | None = None

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not _EMAIL.match(value):
            raise ValueError("Correo no válido")
        return value

    @field_validator("group_id")
    @classmethod
    def _valid_group(cls, value: str | None) -> str | None:
        if value is not None and not _DIGITS.match(value):
            raise ValueError("Id de grupo no válido")
        return value

    @model_validator(mode="after")
    def _exactly_one(self) -> "Recipient":
        if (self.email is None) == (self.group_id is None):
            raise ValueError("Indique un correo o un grupo, no ambos")
        return self

    @property
    def key(self) -> str:
        return self.email or f"group-{self.group_id}"


class ShareCreate(BaseModel):
    recipients: list[Recipient] = Field(min_length=1, max_length=50)
    access_level: AccessLevel
    send_email: bool = False
    subject: str | None = Field(default=None, max_length=200)
    message: str | None = Field(default=None, max_length=2000)


class ShareUpdate(BaseModel):
    access_level: AccessLevel


class SkippedRecipient(BaseModel):
    recipient: Recipient
    reason: str
    current_level: AccessLevel | None = None


class ShareCreateResult(BaseModel):
    created: list[Share]
    skipped: list[SkippedRecipient]
