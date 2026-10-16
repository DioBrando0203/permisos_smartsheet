from datetime import datetime

from pydantic import BaseModel

from app.services.permissions import AccessLevel, LockedReason, ShareScope, ShareType


class Me(BaseModel):
    user_id: str
    email: str
    name: str | None = None
    account_name: str | None = None
    is_system_admin: bool


class Person(BaseModel):
    """Persona o grupo del directorio: contacto, usuario de la organización o con acceso."""

    key: str
    type: ShareType
    name: str | None = None
    email: str | None = None
    sheet_count: int
    highest_level: AccessLevel | None = None
    is_contact: bool
    is_org_member: bool
    is_token_owner: bool
    # Sólo para usuarios de la organización: Smartsheet no lo da de colaboradores externos.
    last_login: datetime | None = None


class FailedSheet(BaseModel):
    sheet_id: str
    sheet_name: str
    code: str


class PeopleResponse(BaseModel):
    people: list[Person]
    total: int
    incomplete: bool
    failed_sheets: list[FailedSheet]
    loaded_at: datetime | None = None


class PersonSheetAccess(BaseModel):
    sheet_id: str
    sheet_name: str
    share_id: str
    access_level: AccessLevel
    scope: ShareScope
    editable: bool
    locked_reason: LockedReason | None = None


class PersonDetail(BaseModel):
    person: Person
    sheets: list[PersonSheetAccess]


class Group(BaseModel):
    id: str
    name: str
    description: str | None = None
    member_count: int | None = None


class Contact(BaseModel):
    id: str
    email: str
    name: str | None = None
