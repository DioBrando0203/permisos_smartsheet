"""Paso del procesador que crea y mantiene cada hoja hija (SPEC-B18, SPEC-B19); nunca borra."""

import time
from collections.abc import Awaitable, Callable
from dataclasses import replace

from app.core.config import Settings
from app.services.childsheets import rules
from app.services.childsheets.rules import KEY, ROW_TYPE, ChildSpec
from app.services.childsheets.specs import BILLING, RECORDS
from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.runtime import writes_allowed
from app.services.smartsheet import RawRow, SmartsheetClient
from app.services.smartsheet.types import RawColumn


class ChildSheetSync:
    def __init__(
        self,
        settings: Settings,
        client: SmartsheetClient,
        spec: ChildSpec,
        sheet: str,
        *,
        interval: float = 30.0,
        max_rows: int = 20,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.client = client
        self.spec = spec
        self.sheet = sheet
        self.interval = max(0.0, interval)
        self.max_rows = max(1, max_rows)
        self.clock = clock
        self.last: dict | None = None
        self._last_at: float | None = None

    async def run(self) -> dict:
        """Una pasada; entre pasadas espera al menos `interval`."""
        now = self.clock()
        if self.last is not None and self._last_at is not None:
            if now - self._last_at < self.interval:
                return self.last
        self._last_at = now
        await self._check_barriers()
        spec = self.spec
        master = await self._columns(pilot.PRESENTABLE, (*spec.triggers, *spec.context))
        child = await self._columns(self.sheet, (KEY, *spec.mirrored))
        initial = [t for t in spec.initial if t in master and t in child]
        # El resumen sólo vuelve a columnas de la maestra que no son fórmula.
        summary = [t for t in spec.summary if t in child and t in master and not master[t].formula]
        masters = await self._masters(master, [*spec.context, *initial, *summary])
        children = await self._children(child, [*spec.mirrored, *summary])
        plan = rules.plan(replace(spec, summary=tuple(summary)), masters, children)
        add = [
            self._row(None, m.values, child, (KEY, *spec.mirrored, *initial), m.row_id)
            for m in plan.create[: self.max_rows]
        ]
        changes = [
            self._row(row_id, v, child, tuple(v)) for row_id, v in plan.update[: self.max_rows]
        ]
        back = [
            self._row(row_id, v, master, tuple(v)) for row_id, v in plan.summary[: self.max_rows]
        ]
        if add or changes:
            await self.client.upsert_catalog_rows(self.sheet, add, changes)
        if back:
            await self.client.upsert_catalog_rows(pilot.PRESENTABLE, [], back)
        pending = len(plan.create) + len(plan.update) + len(plan.summary)
        self.last = {
            "created": len(add),
            "updated": len(changes),
            "summarized": len(back),
            "waiting": plan.waiting,
            "deferred": pending - len(add) - len(changes) - len(back),
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
        self, cols: dict[str, RawColumn], titles: list[str]
    ) -> list[rules.MasterRow]:
        triggers = self.spec.triggers
        wanted = [cols[t].id for t in dict.fromkeys([*triggers, *titles])]
        result = []
        for row in await self.client.list_rows(pilot.PRESENTABLE, wanted, objects=True):
            values = {title: _value(row, cols[title]) for title in titles}
            if ROW_TYPE in self.spec.derived:
                values[ROW_TYPE] = "Permit" if row.parent_id else "Project"
            needed = any(_value(row, cols[t]) for t in triggers) if triggers else True
            result.append(rules.MasterRow(row.id, needed, values))
        return result

    async def _children(
        self, cols: dict[str, RawColumn], titles: list[str]
    ) -> list[rules.ChildRow]:
        wanted = [cols[t].id for t in (KEY, *titles)]
        rows = await self.client.list_rows(self.sheet, wanted, objects=True)
        return [
            rules.ChildRow(
                row.id, str(_value(row, cols[KEY])), {t: _value(row, cols[t]) for t in titles}
            )
            for row in rows
            if _value(row, cols[KEY])
        ]

    def _row(
        self,
        row_id: str | None,
        values: dict,
        cols: dict[str, RawColumn],
        titles: tuple,
        key: str = "",
    ) -> dict:
        """Fila nueva (`row_id` None, sólo celdas con valor) o cambios (vacío como "")."""
        cells = []
        for title in titles:
            value = key if title == KEY else values.get(title)
            if row_id is None and value in (None, "", False):
                continue
            cells.append({"columnId": int(cols[title].id), "value": "" if value is None else value})
        return (
            {"toBottom": True, "cells": cells}
            if row_id is None
            else {"id": int(row_id), "cells": cells}
        )


def _value(row: RawRow, column: RawColumn) -> rules.Value:
    """Fecha ISO, casilla booleana, correo de un contacto o texto visible; vacío como None."""
    if column.type == "CONTACT_LIST" and column.id in row.contacts:
        return row.contacts[column.id]
    if column.type == "DATE":
        found = row.date_cells.get(column.id)
        return found.isoformat() if found else None
    text = (row.cells.get(column.id) or "").strip()
    if column.type == "CHECKBOX":
        return text.lower() == "true"
    return text or None


def child_hooks(
    settings: Settings, client: SmartsheetClient
) -> dict[str, Callable[[], Awaitable[dict]]]:
    """Pasos del procesador por hoja hija activada; vacío sin barreras de escritura."""
    if not writes_allowed(settings):
        return {}
    configured = [
        (RECORDS, settings.app_records_sync_enabled, settings.app_records_sheet_id),
        (BILLING, settings.app_billing_sync_enabled, settings.app_billing_sheet_id),
    ]
    return {
        spec.name: ChildSheetSync(
            settings,
            client,
            spec,
            sheet,
            interval=settings.app_records_interval_seconds,
            max_rows=settings.app_records_max_rows,
        ).run
        for spec, enabled, sheet in configured
        if enabled and sheet
    }
