"""Datos internos ya mapeados desde Smartsheet. Ids siempre como texto (ADR-B07)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.services.permissions import AccessLevel, ShareScope, ShareType


@dataclass(frozen=True)
class RawSheet:
    id: str
    name: str
    # None: hoja de otra persona de la organización, no compartida con el token (PEN-14).
    access_level: AccessLevel | None
    permalink: str | None
    modified_at: datetime | None
    owner_email: str | None = None
    in_my_list: bool = True


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
    last_login: datetime | None = None


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


@dataclass(frozen=True)
class RawAuthor:
    email: str | None
    name: str | None


@dataclass(frozen=True)
class RawColumn:
    id: str
    title: str
    index: int
    primary: bool
    type: str | None = None


@dataclass(frozen=True)
class RawRow:
    """Fila con su autoría: sólo la última modificación, no el historial completo."""

    id: str
    row_number: int | None
    label: str | None
    created_at: datetime | None
    created_by: RawAuthor | None
    modified_at: datetime | None
    modified_by: RawAuthor | None
    # Texto visible por id de columna, sólo de las columnas pedidas.
    cells: dict[str, str | None] = field(default_factory=dict)


@dataclass(frozen=True)
class RawCellChange:
    column_id: str
    value: str | None
    modified_at: datetime | None
    modified_by: RawAuthor | None
