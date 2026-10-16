"""Listado y detalle de hojas: las del token y, como administrador, las de toda la organización.

SPEC-B01 y PEN-14: las hojas de otras personas no compartidas con el token sólo se consultan.
"""

from dataclasses import replace
from typing import Literal

from app.core.errors import AppError
from app.models.sheets import SheetList, SheetSummary
from app.services.cache import TtlCache
from app.services.permissions import can_manage_shares
from app.services.search import matches, normalize
from app.services.smartsheet import RawColumn, RawSheet, SmartsheetClient

SHEETS_KEY = "sheets"
SheetScope = Literal["all", "mine", "org_only"]


class SheetService:
    def __init__(
        self,
        client: SmartsheetClient,
        cache: TtlCache,
        dynamic_view_sheets: frozenset[str] = frozenset(),
    ) -> None:
        self._client = client
        self._cache = cache
        self._dynamic_view_sheets = dynamic_view_sheets

    async def raw_sheets(self, *, refresh: bool = False) -> list[RawSheet]:
        sheets = await self._cache.get_or_load(SHEETS_KEY, self._load, refresh=refresh)
        return sorted(sheets, key=lambda sheet: normalize(sheet.name))

    async def list(
        self, query: str | None, scope: SheetScope = "all", *, refresh: bool = False
    ) -> SheetList:
        sheets = await self.raw_sheets(refresh=refresh)
        wanted = [sheet for sheet in sheets if _in_scope(sheet, scope)]
        found = [self.summary(sheet) for sheet in wanted if matches(query, sheet.name)]
        return SheetList(
            sheets=found,
            total=len(sheets),
            total_mine=sum(1 for sheet in sheets if sheet.in_my_list),
            loaded_at=self._cache.loaded_at(SHEETS_KEY),
        )

    async def _load(self) -> list[RawSheet]:
        """Hojas del token más las de la organización que no están en su lista."""
        mine = await self._client.list_sheets()
        org = await self._org_sheets()
        owners = {sheet.id: sheet.owner_email for sheet in org}
        known = {sheet.id for sheet in mine}
        extra = [sheet for sheet in org if sheet.id not in known]
        return [replace(sheet, owner_email=owners.get(sheet.id)) for sheet in mine] + extra

    async def _org_sheets(self) -> list[RawSheet]:
        """Sólo un administrador del sistema las ve; si Smartsheet lo niega, se omiten."""
        try:
            return await self._client.list_org_sheets()
        except AppError as error:
            if error.code in {"SMARTSHEET_FORBIDDEN", "NOT_FOUND"}:
                return []
            raise

    async def find(self, sheet_id: str) -> RawSheet | None:
        return next((sheet for sheet in await self.raw_sheets() if sheet.id == sheet_id), None)

    async def resolve_id(self, sheet_ref: str) -> str:
        """Id numérico tal cual; un código de permalink se busca en el listado (SPEC-B01)."""
        if sheet_ref.isdigit():
            return sheet_ref
        suffix = f"/{sheet_ref}"
        for sheet in await self.raw_sheets():
            if sheet.permalink and sheet.permalink.split("?")[0].endswith(suffix):
                return sheet.id
        raise sheet_not_found()

    async def get(self, sheet_id: str) -> SheetSummary:
        sheet = await self.find(sheet_id)
        if sheet is None:
            raise sheet_not_found()
        return self.summary(sheet)

    async def columns(self, sheet_id: str) -> list[RawColumn]:
        """Columnas de la hoja en su orden, con caché (cambian poco)."""

        async def load() -> list[RawColumn]:
            try:
                return await self._client.list_columns(sheet_id)
            except AppError as error:
                if error.code == "NOT_FOUND":
                    raise sheet_not_found() from None
                raise

        columns = await self._cache.get_or_load(f"columns:{sheet_id}", load)
        return sorted(columns, key=lambda column: column.index)

    def summary(self, sheet: RawSheet) -> SheetSummary:
        return to_summary(sheet, has_dynamic_view=sheet.id in self._dynamic_view_sheets)


def to_summary(sheet: RawSheet, *, has_dynamic_view: bool = False) -> SheetSummary:
    return SheetSummary(
        id=sheet.id,
        name=sheet.name,
        access_level=sheet.access_level,
        can_manage_shares=can_manage_shares(sheet.access_level),
        permalink=sheet.permalink,
        modified_at=sheet.modified_at,
        has_dynamic_view=has_dynamic_view,
        owner_email=sheet.owner_email,
        in_my_list=sheet.in_my_list,
    )


def _in_scope(sheet: RawSheet, scope: SheetScope) -> bool:
    if scope == "mine":
        return sheet.in_my_list
    if scope == "org_only":
        return not sheet.in_my_list
    return True


def sheet_not_found() -> AppError:
    return AppError("SHEET_NOT_FOUND", "La hoja no existe o la cuenta no tiene acceso.", 404)
