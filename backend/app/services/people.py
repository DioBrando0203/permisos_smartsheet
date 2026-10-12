"""Directorio de personas y grupos, vista por persona, contactos y grupos (SPEC-B03).

Lee los permisos de todas las hojas con la concurrencia del cliente; una hoja que falla se
informa en `failed_sheets` y no detiene el resto (Bulkhead).
"""

import asyncio
from dataclasses import dataclass

from app.core.errors import AppError
from app.models.people import (
    Contact,
    FailedSheet,
    Group,
    Me,
    PeopleResponse,
    PersonDetail,
)
from app.services.cache import TtlCache
from app.services.directory import DirectoryEntry, SheetShares, build_directory, sort_people
from app.services.search import matches
from app.services.shares import PEOPLE_KEY, ShareService
from app.services.sheets import SheetService
from app.services.smartsheet import RawContact, RawSheet, RawUser, SmartsheetClient

# Filtros rápidos del directorio: nombre del filtro y condición sobre la persona (P-26).
FILTERS = {
    "contacts": lambda person: person.is_contact,
    "org": lambda person: person.is_org_member,
    "external": lambda person: not person.is_org_member and person.type == "USER",
    "groups": lambda person: person.type == "GROUP",
    "with_access": lambda person: person.sheet_count > 0,
    "without_access": lambda person: person.sheet_count == 0,
}


@dataclass(frozen=True)
class Directory:
    entries: dict[str, DirectoryEntry]
    failed: list[FailedSheet]
    token_email: str | None


class PeopleService:
    def __init__(
        self,
        client: SmartsheetClient,
        cache: TtlCache,
        sheets: SheetService,
        shares: ShareService,
    ) -> None:
        self._client = client
        self._cache = cache
        self._sheets = sheets
        self._shares = shares

    async def me(self) -> Me:
        raw = await self._cache.get_or_load("me", self._client.get_me)
        return Me(
            user_id=raw.user_id,
            email=raw.email,
            name=raw.name,
            account_name=raw.account_name,
            is_system_admin=raw.is_system_admin,
        )

    async def list(
        self, query: str | None, only: str | None, *, refresh: bool = False
    ) -> PeopleResponse:
        directory = await self._directory(refresh=refresh)
        people = [entry.to_person(directory.token_email) for entry in directory.entries.values()]
        condition = FILTERS.get(only or "")
        found = [
            person
            for person in people
            if matches(query, person.name, person.email) and (not condition or condition(person))
        ]
        return PeopleResponse(
            people=sort_people(found),
            total=len(people),
            incomplete=bool(directory.failed),
            failed_sheets=directory.failed,
            loaded_at=self._cache.loaded_at(PEOPLE_KEY),
        )

    async def detail(self, key: str) -> PersonDetail:
        directory = await self._directory()
        entry = directory.entries.get(key.strip().lower() if "@" in key else key)
        if entry is None:
            raise AppError("PERSON_NOT_FOUND", "No se encontró a esa persona o grupo.", 404)
        sheets = sorted(entry.accesses, key=lambda access: access.sheet_name.casefold())
        return PersonDetail(person=entry.to_person(directory.token_email), sheets=sheets)

    async def contacts(self, *, refresh: bool = False) -> list[Contact]:
        raw = await self._cache.get_or_load("contacts", self._client.list_contacts, refresh=refresh)
        return [Contact(id=item.id, email=item.email, name=item.name) for item in raw]

    async def groups(self, *, refresh: bool = False) -> list[Group]:
        raw = await self._cache.get_or_load("groups", self._client.list_groups, refresh=refresh)
        return [
            Group(id=g.id, name=g.name, description=g.description, member_count=g.member_count)
            for g in raw
        ]

    async def _directory(self, *, refresh: bool = False) -> Directory:
        async def load() -> Directory:
            return await self._build(refresh)

        return await self._cache.get_or_load(PEOPLE_KEY, load, refresh=refresh)

    async def _build(self, refresh: bool) -> Directory:
        sheets = await self._sheets.raw_sheets(refresh=refresh)
        results = await asyncio.gather(*(self._sheet_shares(sheet, refresh) for sheet in sheets))
        loaded = [item for item in results if isinstance(item, SheetShares)]
        failed = [item for item in results if isinstance(item, FailedSheet)]
        contacts = await self._optional(self._client.list_contacts)
        org_users = await self._optional(self._client.list_users)
        me = await self.me()
        entries = build_directory(loaded, contacts, org_users)
        return Directory(entries=entries, failed=failed, token_email=me.email)

    async def _sheet_shares(self, sheet: RawSheet, refresh: bool) -> SheetShares | FailedSheet:
        try:
            shares = await self._shares.raw_shares(sheet.id, refresh=refresh)
        except AppError as error:
            return FailedSheet(sheet_id=sheet.id, sheet_name=sheet.name, code=error.code)
        return SheetShares(sheet=sheet, shares=shares)

    async def _optional(self, loader) -> list[RawContact] | list[RawUser]:
        """Contactos y usuarios enriquecen el directorio; si Smartsheet los niega, se omiten."""
        try:
            return await loader()
        except AppError as error:
            if error.code in {"SMARTSHEET_FORBIDDEN", "NOT_FOUND"}:
                return []
            raise
