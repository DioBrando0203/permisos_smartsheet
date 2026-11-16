"""Lectura y escritura de celdas y barreras comunes a los pasos sobre la maestra y sus hojas."""

import time
from collections.abc import Callable

from app.core.config import Settings
from app.services.childsheets import rules
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.runtime import writes_allowed
from app.services.smartsheet import RawRow, SmartsheetClient
from app.services.smartsheet.mappers import EMAIL_SEPARATOR
from app.services.smartsheet.types import RawColumn

MULTI_CONTACT = "MULTI_CONTACT_LIST"
# Nivel de la API que muestra las columnas de varios contactos con su tipo y sus correos.
LEVEL = 2


async def check_barriers(settings: Settings, client: SmartsheetClient, *sheets: str) -> None:
    """Escritura aprobada y cada hoja configurada y dentro de Pruebas; si no, ValueError."""
    if not writes_allowed(settings) or not all(sheets):
        raise ValueError("Escritura deshabilitada por las barreras del servicio")
    for sheet in sheets:
        if await client.sheet_workspace_id(sheet) != PILOT_WORKSPACE:
            raise ValueError("La hoja no pertenece al workspace Pruebas")


async def columns(
    client: SmartsheetClient, sheet: str, required: tuple[str, ...]
) -> dict[str, RawColumn]:
    """Columnas únicas por título; las requeridas deben existir una sola vez."""
    found = await client.list_columns(sheet, level=LEVEL)
    titles = [column.title for column in found]
    if any(titles.count(title) != 1 for title in required):
        raise ValueError("Columnas requeridas ausentes o duplicadas")
    return {column.title: column for column in found if titles.count(column.title) == 1}


def cell(column: RawColumn, value: rules.Value) -> dict:
    """Celda a escribir; varios contactos van como `objectValue` con sus correos."""
    if column.type == MULTI_CONTACT and isinstance(value, str) and value:
        contacts = [
            {"objectType": "CONTACT", "email": email} for email in value.split(EMAIL_SEPARATOR)
        ]
        return {
            "columnId": int(column.id),
            "objectValue": {"objectType": "MULTI_CONTACT", "values": contacts},
        }
    return {"columnId": int(column.id), "value": "" if value is None else value}


def value(row: RawRow, column: RawColumn) -> rules.Value:
    """Fecha ISO, casilla booleana, correo de un contacto o texto visible; vacío como None.

    De varios contactos sólo cuentan los que tienen correo: un nombre suelto no se copia.
    """
    if column.type == MULTI_CONTACT:
        return row.contacts.get(column.id)
    if column.type == "CONTACT_LIST" and column.id in row.contacts:
        return row.contacts[column.id]
    if column.type == "DATE":
        found = row.date_cells.get(column.id)
        return found.isoformat() if found else None
    text = (row.cells.get(column.id) or "").strip()
    if column.type == "CHECKBOX":
        return text.lower() == "true"
    return text or None


class Paced:
    """Paso que corre como mucho una vez por `interval` y repite su último resultado."""

    def __init__(self, interval: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.interval = max(0.0, interval)
        self.clock = clock
        self.last: dict | None = None
        self._last_at: float | None = None

    def due(self) -> bool:
        now = self.clock()
        if self.last is not None and self._last_at is not None:
            if now - self._last_at < self.interval:
                return False
        self._last_at = now
        return True
