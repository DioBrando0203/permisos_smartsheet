"""Hijas de la maestra con los datos de su proyecto (SPEC-B20 HP-07): sólo celdas vacías.

Una hija creada desde una Dynamic View llega sin los datos del proyecto; al quedar bajo su
madre (ID-51) los toma de ella. Nunca reemplaza un valor que la hija ya tiene.
"""

from app.core.config import Settings
from app.services.childsheets import rules
from app.services.childsheets.cells import LEVEL, Paced, cell, check_barriers, columns, value
from app.services.childsheets.specs import INHERITED
from app.services.ids import pilot
from app.services.smartsheet import SmartsheetClient


class InheritSync(Paced):
    def __init__(
        self,
        settings: Settings,
        client: SmartsheetClient,
        *,
        interval: float = 30.0,
        max_rows: int = 20,
    ) -> None:
        super().__init__(interval)
        self.settings = settings
        self.client = client
        self.max_rows = max(1, max_rows)

    async def run(self) -> dict:
        if not self.due():
            return self.last or {}
        await check_barriers(self.settings, self.client, pilot.PRESENTABLE)
        cols = await columns(self.client, pilot.PRESENTABLE, ())
        titles = tuple(t for t in INHERITED if t in cols and not cols[t].formula)
        plan: list = []
        if titles:
            wanted = [cols[t].id for t in titles]
            rows = await self.client.list_rows(pilot.PRESENTABLE, wanted, objects=True, level=LEVEL)
            found = {row.id: {t: value(row, cols[t]) for t in titles} for row in rows}
            family = pilot.split_hierarchy(rows)[1]
            plan = rules.inherit_plan(
                [(child.id, found[child.id], found.get(root, {})) for child, root in family],
                titles,
            )
        updates = [
            {"id": int(row_id), "cells": [cell(cols[t], v) for t, v in missing.items()]}
            for row_id, missing in plan[: self.max_rows]
        ]
        if updates:
            await self.client.upsert_catalog_rows(pilot.PRESENTABLE, [], updates)
        self.last = {"filled": len(updates), "deferred": len(plan) - len(updates)}
        return self.last
