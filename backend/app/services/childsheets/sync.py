"""Paso del procesador que crea y mantiene cada hoja hija (SPEC-B18, SPEC-B19, SPEC-B20).

Nunca borra filas.
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import replace

from app.core.config import Settings
from app.services.childsheets import rules
from app.services.childsheets.cells import LEVEL, cell, check_barriers, columns, value
from app.services.childsheets.inherit import InheritSync
from app.services.childsheets.options import ProjectOptions
from app.services.childsheets.rules import KEY, ROW_TYPE, ChildSpec
from app.services.childsheets.specs import BILLING, DESIGN_TICKETS, MOT, PERMITS, RECORDS
from app.services.ids import pilot
from app.services.ids.runtime import writes_allowed
from app.services.smartsheet import SmartsheetClient
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
        await check_barriers(self.settings, self.client, pilot.PRESENTABLE, self.sheet)
        spec = self.spec
        required = (*spec.triggers, *spec.reads, *spec.context)
        master = await columns(self.client, pilot.PRESENTABLE, required)
        child = await columns(self.client, self.sheet, (KEY, *spec.mirrored))
        initial = [t for t in spec.initial if t in master and t in child]
        # El resumen sólo vuelve a columnas de la maestra que no son fórmula.
        pairs = tuple(
            (mine, theirs)
            for mine, theirs in spec.summary_pairs
            if mine in child and theirs in master and not master[theirs].formula
        )
        cancel = spec.cancel if spec.cancel and spec.cancel[0] in child else None
        spec = replace(spec, summary=pairs, cancel=cancel)
        backs = [theirs for _, theirs in pairs]
        masters = await self._masters(master, [*spec.context, *initial, *backs])
        mine = [m for m, _ in pairs] + ([cancel[0]] if cancel else [])
        children = await self._children(child, [*spec.mirrored, *mine])
        plan = rules.plan(spec, masters, children)
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

    async def _masters(
        self, cols: dict[str, RawColumn], titles: list[str]
    ) -> list[rules.MasterRow]:
        spec = self.spec
        names = list(dict.fromkeys([*titles, *spec.reads]))
        wanted = [cols[t].id for t in dict.fromkeys([*spec.triggers, *names])]
        rows = await self.client.list_rows(pilot.PRESENTABLE, wanted, objects=True, level=LEVEL)
        found = {row.id: {title: value(row, cols[title]) for title in names} for row in rows}
        roots = {child.id: root for child, root in pilot.split_hierarchy(rows)[1]}
        result = []
        for row in rows:
            values, is_child = found[row.id], row.id in roots
            if is_child and spec.fallback:
                values = rules.with_fallback(values, found.get(roots[row.id], {}), spec.fallback)
            if ROW_TYPE in spec.derived:
                values[ROW_TYPE] = spec.kind(values, bool(row.parent_id))
            if spec.when is not None:
                needed = spec.when(values, is_child)
            elif spec.triggers:
                needed = any(value(row, cols[t]) for t in spec.triggers)
            else:
                needed = True
            result.append(rules.MasterRow(row.id, needed, values, is_child))
        return result

    async def _children(
        self, cols: dict[str, RawColumn], titles: list[str]
    ) -> list[rules.ChildRow]:
        titles = list(dict.fromkeys(titles))
        wanted = [cols[t].id for t in (KEY, *titles)]
        rows = await self.client.list_rows(self.sheet, wanted, objects=True, level=LEVEL)
        return [
            rules.ChildRow(
                row.id, str(value(row, cols[KEY])), {t: value(row, cols[t]) for t in titles}
            )
            for row in rows
            if value(row, cols[KEY])
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
            found = key if title == KEY else values.get(title)
            if row_id is None and found in (None, "", False):
                continue
            cells.append(cell(cols[title], found))
        return (
            {"toBottom": True, "cells": cells}
            if row_id is None
            else {"id": int(row_id), "cells": cells}
        )


def child_hooks(
    settings: Settings, client: SmartsheetClient
) -> dict[str, Callable[[], Awaitable[dict]]]:
    """Pasos del procesador activados, en orden; vacío sin barreras de escritura.

    Primero las hijas toman los datos de su proyecto; al final, las listas de proyectos.
    """
    if not writes_allowed(settings):
        return {}
    interval, max_rows = settings.app_records_interval_seconds, settings.app_records_max_rows
    hooks: dict[str, Callable[[], Awaitable[dict]]] = {}
    if settings.app_inherit_enabled:
        hooks["inherit"] = InheritSync(settings, client, interval=interval, max_rows=max_rows).run
    configured = [
        (RECORDS, settings.app_records_sync_enabled, settings.app_records_sheet_id),
        (BILLING, settings.app_billing_sync_enabled, settings.app_billing_sheet_id),
        (PERMITS, settings.app_permits_sync_enabled, settings.app_permits_sheet_id),
        (MOT, settings.app_mot_sync_enabled, settings.app_mot_sheet_id),
        (
            DESIGN_TICKETS,
            settings.app_design_tickets_sync_enabled,
            settings.app_design_tickets_sheet_id,
        ),
    ]
    for spec, enabled, sheet in configured:
        if enabled and sheet:
            hooks[spec.name] = ChildSheetSync(
                settings, client, spec, sheet, interval=interval, max_rows=max_rows
            ).run
    if settings.ids_project_options_enabled:
        hooks["options"] = ProjectOptions(settings, client, interval=interval).run
    return hooks
