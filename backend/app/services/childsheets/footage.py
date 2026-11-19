"""Metraje en la maestra y en `Billing`, con aviso de lo que cambia facturación (SPEC-B19 FH-05c).

Diseño lo llena en la maestra y facturación lo puede corregir en `Billing`. Si una celda difiere,
gana la hoja que la cambió más tarde (historial de celdas); con `Billing` vacío gana la maestra
sin consultar. Si gana `Billing`, el valor pasa a la maestra y Smartsheet manda por correo la fila
con el valor anterior y el nuevo a las personas activas de `Contact List` del equipo
`Footage Alerts`. Nada se escribe como nota en las hojas; cada cambio queda en el log.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from app.core.config import Settings
from app.services.childsheets.cells import LEVEL, Paced, cell, check_barriers, columns, value
from app.services.childsheets.contacts import read_people, team_options
from app.services.childsheets.rules import KEY, Value
from app.services.childsheets.specs import FOOTAGE
from app.services.ids import pilot
from app.services.smartsheet import SmartsheetClient
from app.services.smartsheet.types import RawColumn

logger = logging.getLogger(__name__)
ALERT_TEAM = "Footage Alerts"
CONTEXT = ("Tracking Project", "Project Name")


@dataclass(frozen=True)
class Change:
    column: str
    before: Value
    after: Value


def norm(found: Value) -> Value:
    """Vacío y ausente cuentan igual; el texto se compara sin espacios de los bordes."""
    if isinstance(found, str):
        return found.strip() or None
    return found


def billing_wins(master_at: datetime | None, billing_at: datetime | None) -> bool:
    """Gana la hoja que cambió más tarde; sin historial en `Billing`, la maestra."""
    if billing_at is None:
        return False
    return master_at is None or billing_at > master_at


def notice(tracking: Value, name: Value, changes: list[Change]) -> tuple[str, str]:
    """Asunto y mensaje del correo, en inglés y sin texto técnico."""
    subject = f"Footage updated in Billing: {tracking or ''} – {name or ''}"
    lines = [
        f"{c.column}: {norm(c.before) or '(blank)'} → {norm(c.after) or '(blank)'}" for c in changes
    ]
    message = "Billing changed the footage of this project.\n\n" + "\n".join(lines)
    return subject, message


class FootageSync(Paced):
    def __init__(
        self,
        settings: Settings,
        client: SmartsheetClient,
        *,
        interval: float = 30.0,
        max_cells: int = 10,
    ) -> None:
        super().__init__(interval)
        self.settings = settings
        self.client = client
        self.max_cells = max(1, max_cells)

    async def run(self) -> dict:
        if not self.due():
            return self.last or {}
        billing = self.settings.app_billing_sheet_id
        await check_barriers(self.settings, self.client, pilot.PRESENTABLE, billing)
        mcols = await columns(self.client, pilot.PRESENTABLE, (*CONTEXT, *FOOTAGE))
        bcols = await columns(self.client, billing, (KEY, *FOOTAGE))
        masters = await self._read(pilot.PRESENTABLE, mcols, (*CONTEXT, *FOOTAGE))
        rows = await self._read(billing, bcols, (KEY, *FOOTAGE))
        to_master, to_billing, notices = [], [], []
        checked = deferred = 0
        for brow, bvals in rows.items():
            mrow = str(bvals.get(KEY) or "")
            mvals = masters.get(mrow)
            diff = [t for t in FOOTAGE if mvals and norm(mvals.get(t)) != norm(bvals.get(t))]
            if not diff:
                continue
            if checked >= self.max_cells:
                deferred += 1
                continue
            mfix, bfix, changes = {}, {}, []
            for title in diff:
                if norm(bvals.get(title)) is not None:
                    checked += 1
                    mine = await self._changed_at(pilot.PRESENTABLE, mrow, mcols[title])
                    theirs = await self._changed_at(billing, brow, bcols[title])
                    if billing_wins(mine, theirs):
                        mfix[title] = bvals.get(title)
                        changes.append(Change(title, mvals.get(title), bvals.get(title)))
                        continue
                bfix[title] = mvals.get(title)
            if mfix:
                to_master.append(_row(mrow, mfix, mcols))
                notices.append((brow, mvals, changes))
            if bfix:
                to_billing.append(_row(brow, bfix, bcols))
        if to_master:
            await self.client.upsert_catalog_rows(pilot.PRESENTABLE, [], to_master)
        if to_billing:
            await self.client.upsert_catalog_rows(billing, [], to_billing)
        notified = await self._notify(billing, bcols, notices)
        self.last = {
            "to_master": len(to_master),
            "to_billing": len(to_billing),
            "notified": notified,
            "deferred": deferred,
        }
        return self.last

    async def _read(
        self, sheet: str, cols: dict[str, RawColumn], titles: tuple[str, ...]
    ) -> dict[str, dict[str, Value]]:
        wanted = [cols[title].id for title in titles]
        rows = await self.client.list_rows(sheet, wanted, objects=True, level=LEVEL)
        return {row.id: {t: value(row, cols[t]) for t in titles} for row in rows}

    async def _changed_at(self, sheet: str, row: str, column: RawColumn) -> datetime | None:
        history = await self.client.get_cell_history(sheet, row, column.id)
        moments = [change.modified_at for change in history if change.modified_at]
        return max(moments) if moments else None

    async def _notify(self, billing: str, bcols: dict[str, RawColumn], notices: list) -> int:
        for _, mvals, changes in notices:
            for change in changes:
                logger.info(
                    "footage: %s %s %r -> %r",
                    mvals.get("Tracking Project"),
                    change.column,
                    change.before,
                    change.after,
                )
        directory = self.settings.app_contacts_sheet_id
        if not notices or not directory:
            return 0
        people = await read_people(self.client, directory)
        recipients = [email for _, email in team_options(people, ALERT_TEAM)]
        if not recipients:
            logger.warning("footage: nadie activo en %s; cambios sin correo", ALERT_TEAM)
            return 0
        shown = [bcols[t].id for t in (*CONTEXT, *FOOTAGE) if t in bcols]
        for brow, mvals, changes in notices:
            subject, message = notice(
                mvals.get("Tracking Project"), mvals.get("Project Name"), changes
            )
            await self.client.send_rows_email(billing, [brow], recipients, subject, message, shown)
        return len(notices)


def _row(row_id: str, values: dict[str, Value], cols: dict[str, RawColumn]) -> dict:
    return {"id": int(row_id), "cells": [cell(cols[t], found) for t, found in values.items()]}
