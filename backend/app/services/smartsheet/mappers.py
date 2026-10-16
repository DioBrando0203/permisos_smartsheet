"""Traduce el JSON de Smartsheet a dataclasses propias (capa anticorrupción, SM-03).

Único lugar que conoce los nombres camelCase y las rarezas de la API: ids numéricos o de
texto, `name` ausente y fechas ISO con `Z`.
"""

from datetime import datetime
from typing import Any

from app.services.permissions import AccessLevel, ShareScope, ShareType
from app.services.smartsheet.types import (
    RawAuthor,
    RawAutomation,
    RawCellChange,
    RawColumn,
    RawContact,
    RawGroup,
    RawMe,
    RawRow,
    RawShare,
    RawSheet,
    RawUser,
)

# JSON de una librería externa sin tipos: se acota a este módulo (PY-11).
Json = dict[str, Any]


def to_sheet(data: Json) -> RawSheet:
    return RawSheet(
        id=_id(data["id"]),
        name=str(data.get("name") or ""),
        access_level=AccessLevel(data["accessLevel"]),
        permalink=data.get("permalink"),
        modified_at=_date(data.get("modifiedAt")),
    )


def to_org_sheet(data: Json) -> RawSheet:
    """Hoja de `/users/sheets`: sólo id, nombre y dueño; sin nivel, enlace ni fecha."""
    return RawSheet(
        id=_id(data["id"]),
        name=str(data.get("name") or ""),
        access_level=None,
        permalink=None,
        modified_at=None,
        owner_email=_email(data.get("owner")),
        in_my_list=False,
    )


def to_share(data: Json) -> RawShare:
    return RawShare(
        id=str(data["id"]),
        type=ShareType(data.get("type", ShareType.USER)),
        user_id=_optional_id(data.get("userId")),
        group_id=_optional_id(data.get("groupId")),
        email=_email(data.get("email")),
        name=_text(data.get("name")),
        access_level=AccessLevel(data["accessLevel"]),
        scope=ShareScope(data.get("scope", ShareScope.ITEM)),
    )


def to_user(data: Json) -> RawUser:
    full_name = _text(data.get("name")) or _join(data.get("firstName"), data.get("lastName"))
    return RawUser(
        id=_id(data["id"]),
        email=_email(data.get("email")) or "",
        name=full_name,
        is_admin=bool(data.get("admin")),
        status=data.get("status"),
        last_login=_date(data.get("lastLogin")),
    )


def to_group(data: Json) -> RawGroup:
    members = data.get("members")
    count = data.get("memberCount")
    if count is None and isinstance(members, list):
        count = len(members)
    return RawGroup(
        id=_id(data["id"]),
        name=str(data.get("name") or ""),
        description=_text(data.get("description")),
        member_count=count,
    )


def to_contact(data: Json) -> RawContact:
    return RawContact(
        id=str(data["id"]), email=_email(data.get("email")) or "", name=_text(data.get("name"))
    )


def to_me(data: Json) -> RawMe:
    account = data.get("account") or {}
    return RawMe(
        user_id=_id(data["id"]),
        email=_email(data.get("email")) or "",
        name=_join(data.get("firstName"), data.get("lastName")),
        account_name=_text(account.get("name")),
        is_system_admin=bool(data.get("admin")),
    )


def to_column(data: Json) -> RawColumn:
    return RawColumn(
        id=_id(data["id"]),
        title=str(data.get("title") or ""),
        index=int(data.get("index") or 0),
        primary=bool(data.get("primary")),
        type=data.get("type"),
    )


def to_row(data: Json, label_column_id: str | None = None) -> RawRow:
    cells = {_id(cell.get("columnId")): _cell_text(cell) for cell in data.get("cells") or []}
    label = cells.get(label_column_id) if label_column_id else None
    if label is None and label_column_id is None:
        label = next((text for text in cells.values() if text), None)
    return RawRow(
        id=_id(data["id"]),
        row_number=data.get("rowNumber"),
        label=label,
        created_at=_date(data.get("createdAt")),
        created_by=_author(data.get("createdBy")),
        modified_at=_date(data.get("modifiedAt")),
        modified_by=_author(data.get("modifiedBy")),
        cells=cells,
    )


def to_cell_change(data: Json) -> RawCellChange:
    return RawCellChange(
        column_id=_id(data.get("columnId")),
        value=_cell_text(data),
        modified_at=_date(data.get("modifiedAt")),
        modified_by=_author(data.get("modifiedBy")),
    )


def to_automation(data: Json) -> RawAutomation:
    action = data.get("action") or {}
    emails = [_email(item.get("email")) for item in action.get("recipients") or []]
    return RawAutomation(
        id=_id(data["id"]),
        name=str(data.get("name") or ""),
        enabled=bool(data.get("enabled")),
        disabled_reason=_text(data.get("disabledReason")),
        disabled_reason_text=_text(data.get("disabledReasonText")),
        action_type=_text(action.get("type")),
        frequency=_text(action.get("frequency")),
        recipient_emails=[email for email in emails if email],
        recipient_column_ids=[_id(column) for column in action.get("recipientColumnIds") or []],
        notify_all_shared=bool(action.get("notifyAllSharedUsers")),
        modified_at=_date(data.get("modifiedAt")),
        modified_by=_author(data.get("modifiedBy")),
    )


def _cell_text(cell: Json) -> str | None:
    """Lo que ve la persona en la celda: `displayValue` si existe, si no `value`."""
    return _text(cell.get("displayValue", cell.get("value")))


def _author(data: Any) -> RawAuthor | None:
    if not isinstance(data, dict):
        return None
    return RawAuthor(email=_email(data.get("email")), name=_text(data.get("name")))


def _id(value: Any) -> str:
    return str(value)


def _optional_id(value: Any) -> str | None:
    return None if value is None else str(value)


def _text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _email(value: Any) -> str | None:
    text = _text(value)
    return text.lower() if text else None


def _join(first: Any, last: Any) -> str | None:
    return _text(" ".join(part for part in (_text(first), _text(last)) if part))


def _date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
