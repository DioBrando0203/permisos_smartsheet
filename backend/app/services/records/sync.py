"""Paso del procesador que crea y mantiene la hoja hija de Records (SPEC-B18); nunca borra."""

import time
from collections.abc import Awaitable, Callable

from app.core.config import Settings
from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.runtime import writes_allowed
from app.services.records import rules
from app.services.smartsheet import RawRow, SmartsheetClient
from app.services.smartsheet.types import RawColumn


class RecordsSync:
    def __init__(
        self,
        settings: Settings,
        client: SmartsheetClient,
        *,
        interval: float = 30.0,
        max_rows: int = 20,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.client = client
        self.sheet = settings.app_records_sheet_id
        self.interval = max(0.0, interval)
        self.max_rows = max(1, max_rows)
        self.clock = clock
        self.last: dict | None = None
        self._last_at: float | None = None

    async def run(self) -> dict:
        """Una pasada; entre pasadas espera al menos `interval` (RH-11)."""
        now = self.clock()
        if self.last is not None and self._last_at is not None:
            if now - self._last_at < self.interval:
                return self.last
        self._last_at = now
        await self._check_barriers()
        master_cols = await self._columns(pilot.PRESENTABLE, (rules.TRIGGER, *rules.CONTEXT))
        child_cols = await self._columns(self.sheet, (rules.KEY, *rules.CONTEXT))
        initial = [t for t in rules.INITIAL if t in master_cols and t in child_cols]
        masters = await self._masters(master_cols, initial)
        children = await self._children(child_cols)
        plan = rules.plan(masters, children)
        create = plan.create[: self.max_rows]
        update = plan.update[: self.max_rows]
        add = [self._new_row(row, child_cols, initial) for row in create]
        changes = [self._changes(row_id, values, child_cols) for row_id, values in update]
        if add or changes:
            await self.client.upsert_catalog_rows(self.sheet, add, changes)
        self.last = {
            "created": len(add),
            "updated": len(changes),
            "waiting": plan.waiting,
            "deferred": len(plan.create) - len(add) + len(plan.update) - len(update),
        }
        return self.last

    async def _check_barriers(self) -> None:
        if not writes_allowed(self.settings) or not self.sheet:
            raise ValueError("Escritura deshabilitada por las barreras del servicio")
        for sheet in (pilot.PRESENTABLE, self.sheet):
            if await self.client.sheet_workspace_id(sheet) != PILOT_WORKSPACE:
                raise ValueError("La hoja no pertenece al workspace Pruebas")

    async def _columns(self, sheet: str, required: tuple[str, ...]) -> dict[str, RawColumn]:
        columns = await self.client.list_columns(sheet)
        titles = [column.title for column in columns]
        if any(titles.count(title) != 1 for title in required):
            raise ValueError("Columnas requeridas ausentes o duplicadas")
        return {column.title: column for column in columns if titles.count(column.title) == 1}

    async def _masters(
        self, cols: dict[str, RawColumn], initial: list[str]
    ) -> list[rules.MasterRow]:
        titles = (rules.TRIGGER, *rules.CONTEXT, *initial)
        rows = await self.client.list_rows(pilot.PRESENTABLE, [cols[t].id for t in titles])
        return [
            rules.MasterRow(
                row.id,
                _value(row, cols[rules.TRIGGER]) is True,
                {title: _value(row, cols[title]) for title in (*rules.CONTEXT, *initial)},
            )
            for row in rows
        ]

    async def _children(self, cols: dict[str, RawColumn]) -> list[rules.ChildRow]:
        titles = (rules.KEY, *rules.CONTEXT)
        rows = await self.client.list_rows(self.sheet, [cols[t].id for t in titles])
        return [
            rules.ChildRow(
                row.id,
                str(_value(row, cols[rules.KEY]) or ""),
                {title: _value(row, cols[title]) for title in rules.CONTEXT},
            )
            for row in rows
            if _value(row, cols[rules.KEY])
        ]

    def _new_row(
        self, master: rules.MasterRow, cols: dict[str, RawColumn], initial: list[str]
    ) -> dict:
        cells = [{"columnId": int(cols[rules.KEY].id), "value": master.row_id}]
        for title in (*rules.CONTEXT, *initial):
            value = master.values.get(title)
            if value not in (None, "", False):
                cells.append({"columnId": int(cols[title].id), "value": value})
        return {"toBottom": True, "cells": cells}

    def _changes(self, row_id: str, values: dict, cols: dict[str, RawColumn]) -> dict:
        cells = [
            {"columnId": int(cols[title].id), "value": "" if value is None else value}
            for title, value in values.items()
        ]
        return {"id": int(row_id), "cells": cells}


def _value(row: RawRow, column: RawColumn) -> rules.Value:
    """Fecha ISO, casilla booleana o texto visible; vacío como None."""
    if column.type == "DATE":
        found = row.date_cells.get(column.id)
        return found.isoformat() if found else None
    text = (row.cells.get(column.id) or "").strip()
    if column.type == "CHECKBOX":
        return text.lower() == "true"
    return text or None


def records_hook(
    settings: Settings, client: SmartsheetClient
) -> Callable[[], Awaitable[dict]] | None:
    """Paso del procesador; None si está apagado, sin hoja o sin barreras de escritura (RH-10)."""
    if not settings.app_records_sync_enabled or not settings.app_records_sheet_id:
        return None
    if not writes_allowed(settings):
        return None
    sync = RecordsSync(
        settings,
        client,
        interval=settings.app_records_interval_seconds,
        max_rows=settings.app_records_max_rows,
    )
    return sync.run
