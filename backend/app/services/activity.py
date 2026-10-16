"""Actividad de una hoja con datos directos de Smartsheet (SPEC-B08). Sólo lectura.

Fuentes: autoría de cada fila (`include=writerInfo`) e historial de cada celda. No hay API del
"Registro de actividad" de la web y el plan no incluye Event Reporting (B-08).
"""

import asyncio
from datetime import UTC, datetime, timedelta

from app.core.errors import AppError
from app.models.activity import CellChange, RowHistory, SheetActivity
from app.services.activity_rules import (
    LIMITATIONS,
    dominance_warning,
    editor_stats,
    idle_editors,
    rows_since,
    to_author,
    to_changed_row,
)
from app.services.bulk_plans import effective_levels
from app.services.cache import TtlCache
from app.services.shares import ShareService
from app.services.sheets import SheetService
from app.services.smartsheet import RawCellChange, RawColumn, RawRow, SmartsheetClient


class ActivityService:
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

    async def activity(
        self, sheet_id: str, days: int, limit: int, *, refresh: bool = False
    ) -> SheetActivity:
        sheet = await self._sheets.get(sheet_id)
        rows = await self._rows(sheet_id, refresh=refresh)
        people = effective_levels(await self._shares.raw_shares(sheet_id, refresh=refresh))
        since = datetime.now(UTC) - timedelta(days=days)
        recent = rows_since(rows, since)
        editors = editor_stats(recent, people)
        warning = dominance_warning(editors, len(recent))
        return SheetActivity(
            sheet=sheet,
            days=days,
            since=since,
            rows_total=len(rows),
            changed_rows_total=len(recent),
            changed_rows=[to_changed_row(row) for row in recent[:limit]],
            editors=editors,
            idle_editors=idle_editors(recent, people),
            limitations=[warning, *LIMITATIONS] if warning else LIMITATIONS,
        )

    async def row_history(self, sheet_id: str, row_id: str, column_id: str | None) -> RowHistory:
        await self._sheets.get(sheet_id)
        columns = {column.id: column for column in await self._sheets.columns(sheet_id)}
        if column_id is not None and column_id not in columns:
            raise AppError("COLUMN_NOT_FOUND", "La columna no existe en esta hoja.", 404)
        targets = [column_id] if column_id else await self._filled_columns(sheet_id, row_id)
        results = await asyncio.gather(
            *(self._cell_history(sheet_id, row_id, target) for target in targets)
        )
        changes = [
            _cell_change(change, columns)
            for history in results
            if history is not None
            for change in history
        ]
        changes.sort(
            key=lambda item: item.modified_at or datetime.min.replace(tzinfo=UTC), reverse=True
        )
        return RowHistory(
            sheet_id=sheet_id,
            row_id=row_id,
            changes=changes,
            columns_checked=len(targets),
            failed_columns=sum(1 for history in results if history is None),
        )

    async def _rows(self, sheet_id: str, *, refresh: bool) -> list[RawRow]:
        async def load() -> list[RawRow]:
            columns = await self._sheets.columns(sheet_id)
            label = next((c for c in columns if c.primary), columns[0] if columns else None)
            if label is None:
                return []
            return await self._client.list_rows(sheet_id, [label.id], with_authors=True)

        return await self._cache.get_or_load(f"rows:{sheet_id}", load, refresh=refresh)

    async def _filled_columns(self, sheet_id: str, row_id: str) -> list[str]:
        try:
            return await self._client.get_row_filled_columns(sheet_id, row_id)
        except AppError as error:
            if error.code == "NOT_FOUND":
                raise AppError("ROW_NOT_FOUND", "La fila no existe en esta hoja.", 404) from None
            raise

    async def _cell_history(
        self, sheet_id: str, row_id: str, column_id: str
    ) -> list[RawCellChange] | None:
        """Historial de una celda o `None` si falla: una columna no detiene el resto."""
        try:
            return await self._client.get_cell_history(sheet_id, row_id, column_id)
        except AppError:
            return None


def _cell_change(change: RawCellChange, columns: dict[str, RawColumn]) -> CellChange:
    column = columns.get(change.column_id)
    return CellChange(
        column_id=change.column_id,
        column_title=column.title if column else change.column_id,
        value=change.value,
        modified_at=change.modified_at,
        modified_by=to_author(change.modified_by),
    )
