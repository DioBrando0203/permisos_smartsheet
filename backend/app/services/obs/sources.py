"""De qué hoja sale cada comentario de Obs y a qué fila de la maestra va (SPEC-B17 OB-17).

Strategy: el compilador de Obs recorre fuentes con la misma forma (`sheet` y `owners`) y no sabe
de qué hoja viene cada comentario. La maestra es dueña de sus comentarios. Una hoja de equipo es
un reflejo de la maestra: cada fila suya se traduce (Adapter) a su fila de la maestra por
`Master Row`, y desde allí el comentario sigue las mismas reglas que uno escrito en la maestra.
"""

from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.services.childsheets.cells import columns, value
from app.services.childsheets.rules import KEY
from app.services.childsheets.sync import team_sheets
from app.services.smartsheet import SmartsheetClient
from app.services.smartsheet.types import RawComment


class Source(Protocol):
    sheet: str

    async def owners(self, client: SmartsheetClient, rows: set[str]) -> dict[str, str]:
        """Fila de la maestra de cada fila de esta hoja con comentarios por copiar."""
        ...


@dataclass(frozen=True)
class MasterRows:
    """La maestra: cada comentario va al `Obs` de su propia fila."""

    sheet: str

    async def owners(self, client: SmartsheetClient, rows: set[str]) -> dict[str, str]:
        return {row: row for row in rows}


@dataclass(frozen=True)
class MirrorRows:
    """Hoja de equipo: cada fila va al `Obs` de la fila de la maestra que indica `Master Row`."""

    sheet: str

    async def owners(self, client: SmartsheetClient, rows: set[str]) -> dict[str, str]:
        key = (await columns(client, self.sheet, (KEY,)))[KEY]
        found = await client.list_rows(self.sheet, [key.id])
        return {
            row.id: str(master) for row in found if row.id in rows and (master := value(row, key))
        }


@dataclass(frozen=True)
class Entry:
    """Comentario por copiar: la hoja donde está y la fila de la maestra cuyo `Obs` recibe."""

    sheet: str
    target: str
    comment: RawComment


def mirror_sheets(settings: Settings) -> tuple[str, ...]:
    """Hojas de equipo activadas cuya spec pide pasar su chat a `Obs` (hoy sólo `Permits`)."""
    if not settings.app_obs_mirrors_enabled:
        return ()
    return tuple(sheet for spec, sheet in team_sheets(settings) if spec.obs)
