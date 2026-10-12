"""Listado y detalle de hojas accesibles por el token (SPEC-B01)."""

from app.core.errors import AppError
from app.models.sheets import SheetList, SheetSummary
from app.services.cache import TtlCache
from app.services.permissions import can_manage_shares
from app.services.search import matches, normalize
from app.services.smartsheet import RawSheet, SmartsheetClient

SHEETS_KEY = "sheets"


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
        sheets = await self._cache.get_or_load(
            SHEETS_KEY, self._client.list_sheets, refresh=refresh
        )
        return sorted(sheets, key=lambda sheet: normalize(sheet.name))

    async def list(self, query: str | None, *, refresh: bool = False) -> SheetList:
        sheets = await self.raw_sheets(refresh=refresh)
        found = [self.summary(sheet) for sheet in sheets if matches(query, sheet.name)]
        return SheetList(
            sheets=found, total=len(sheets), loaded_at=self._cache.loaded_at(SHEETS_KEY)
        )

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
    )


def sheet_not_found() -> AppError:
    return AppError("SHEET_NOT_FOUND", "La hoja no existe o la cuenta no tiene acceso.", 404)
