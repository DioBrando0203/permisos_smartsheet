"""Agregación pura del directorio: contactos, usuarios de la organización y permisos (ADR-B10).

Une por correo (usuarios) o por id (grupos). Sin E/S: recibe lo ya leído de Smartsheet.
"""

from dataclasses import dataclass, field

from app.models.people import Person, PersonSheetAccess
from app.services.permissions import ShareType, highest, lock_reason
from app.services.smartsheet import RawContact, RawShare, RawSheet, RawUser


@dataclass(frozen=True)
class SheetShares:
    sheet: RawSheet
    shares: list[RawShare]


@dataclass
class DirectoryEntry:
    """Acumulador mutable de una persona o grupo mientras se recorren las hojas."""

    key: str
    type: ShareType
    name: str | None = None
    email: str | None = None
    is_contact: bool = False
    is_org_member: bool = False
    accesses: list[PersonSheetAccess] = field(default_factory=list)

    def to_person(self, token_email: str | None) -> Person:
        levels = [access.access_level for access in self.accesses]
        return Person(
            key=self.key,
            type=self.type,
            name=self.name,
            email=self.email,
            sheet_count=len({access.sheet_id for access in self.accesses}),
            highest_level=highest(levels),
            is_contact=self.is_contact,
            is_org_member=self.is_org_member,
            is_token_owner=bool(self.email and self.email == token_email),
        )


def person_key(share_type: ShareType, email: str | None, item_id: str | None) -> str:
    if share_type is ShareType.GROUP:
        return f"group-{item_id}"
    return email or f"user-{item_id}"


def build_directory(
    sheet_shares: list[SheetShares], contacts: list[RawContact], org_users: list[RawUser]
) -> dict[str, DirectoryEntry]:
    entries: dict[str, DirectoryEntry] = {}
    for contact in contacts:
        entry = _entry(entries, ShareType.USER, contact.email, contact.id, contact.name)
        entry.is_contact = True
    for user in org_users:
        entry = _entry(entries, ShareType.USER, user.email, user.id, user.name)
        entry.is_org_member = True
    for item in sheet_shares:
        for share in item.shares:
            item_id = share.group_id if share.type is ShareType.GROUP else share.user_id
            entry = _entry(entries, share.type, share.email, item_id, share.name)
            entry.accesses.append(_access(item.sheet, share))
    return entries


def _entry(
    entries: dict[str, DirectoryEntry],
    share_type: ShareType,
    email: str | None,
    item_id: str | None,
    name: str | None,
) -> DirectoryEntry:
    key = person_key(share_type, email, item_id)
    entry = entries.setdefault(key, DirectoryEntry(key=key, type=share_type, email=email))
    if name and not entry.name:
        entry.name = name
    return entry


def _access(sheet: RawSheet, share: RawShare) -> PersonSheetAccess:
    reason = lock_reason(share.access_level, share.scope, sheet.access_level)
    return PersonSheetAccess(
        sheet_id=sheet.id,
        sheet_name=sheet.name,
        share_id=share.id,
        access_level=share.access_level,
        scope=share.scope,
        editable=reason is None,
        locked_reason=reason,
    )


def sort_people(people: list[Person]) -> list[Person]:
    return sorted(people, key=lambda person: (-person.sheet_count, _label(person)))


def _label(person: Person) -> str:
    return (person.name or person.email or "").casefold()
