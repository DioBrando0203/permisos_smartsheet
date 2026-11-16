"""Listas de proyectos de la maestra al día (SPEC-ID01 ID-54) para elegirlos desde una vista.

`Parent Project` lista exactamente los proyectos actuales (más recientes primero);
`Linked Tracking` suma los nuevos y conserva los que ya tenía (proyectos de años anteriores).
"""

from app.core.config import Settings
from app.services.childsheets.cells import Paced, check_barriers, columns
from app.services.childsheets.rules import has_id
from app.services.ids import pilot
from app.services.ids.family import PERMIT_TYPES
from app.services.smartsheet import SmartsheetClient

TYPE, STABLE = "Type of Project", "Stable Tracking Project"
# Columna y si su lista es exacta (True) o acumulativa (False).
OPTION_COLUMNS = ((pilot.PARENT_PROJECT, True), ("Linked Tracking", False))


class ProjectOptions(Paced):
    def __init__(
        self, settings: Settings, client: SmartsheetClient, *, interval: float = 30.0
    ) -> None:
        super().__init__(interval)
        self.settings = settings
        self.client = client

    async def run(self) -> dict:
        if not self.due():
            return self.last or {}
        await check_barriers(self.settings, self.client, pilot.PRESENTABLE)
        cols = await columns(self.client, pilot.PRESENTABLE, (TYPE, STABLE))
        rows = await self.client.list_rows(pilot.PRESENTABLE, [cols[TYPE].id, cols[STABLE].id])
        projects = sorted(
            {
                stable
                for row in rows
                if not row.parent_id
                and has_id(stable := (row.cells.get(cols[STABLE].id) or "").strip())
                and (row.cells.get(cols[TYPE].id) or "").strip() not in PERMIT_TYPES
            },
            reverse=True,
        )
        updated = 0
        for title, exact in OPTION_COLUMNS:
            column = cols.get(title)
            if column is None or column.type != "PICKLIST":
                continue
            wanted = projects if exact else sorted({*column.options, *projects}, reverse=True)
            if list(column.options) != wanted:
                await self.client.set_picklist_options(pilot.PRESENTABLE, column.id, wanted)
                updated += 1
        self.last = {"updated": updated, "projects": len(projects)}
        return self.last
