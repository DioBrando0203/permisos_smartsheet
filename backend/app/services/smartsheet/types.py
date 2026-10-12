"""Datos internos ya mapeados desde Smartsheet. Ids siempre como texto (ADR-B07)."""

from dataclasses import dataclass
from datetime import datetime

from app.services.permissions import AccessLevel, ShareScope, ShareType


@dataclass(frozen=True)
class RawSheet:
    id: str
    name: str
    access_level: AccessLevel
    permalink: str | None
    modified_at: datetime | None


@dataclass(frozen=True)
class RawShare:
    id: str
    type: ShareType
    user_id: str | None
    group_id: str | None
    email: str | None
    name: str | None
    access_level: AccessLevel
    scope: ShareScope


@dataclass(frozen=True)
class RawUser:
    id: str
    email: str
    name: str | None
    is_admin: bool
    status: str | None


@dataclass(frozen=True)
class RawGroup:
    id: str
    name: str
    description: str | None
    member_count: int | None


@dataclass(frozen=True)
class RawContact:
    id: str
    email: str
    name: str | None


@dataclass(frozen=True)
class RawMe:
    user_id: str
    email: str
    name: str | None
    account_name: str | None
    is_system_admin: bool


@dataclass(frozen=True)
class NewShare:
    """Destinatario a crear: correo o grupo, con el nivel pedido."""

    email: str | None
    group_id: str | None
    access_level: AccessLevel


@dataclass(frozen=True)
class ShareMessage:
    """Aviso por correo al dar acceso; su sola presencia activa `sendEmail=true` (SM-07)."""

    subject: str | None
    message: str | None
