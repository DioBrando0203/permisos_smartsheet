"""Saltar un paso cuando sus hojas no cambiaron (SPEC-B21 CA-03, CA-04).

`VersionBoard` lee la versión de cada hoja una sola vez por pasada (vale unos segundos) aunque
varios pasos la pidan. `GatedStep` envuelve un paso: si ninguna de sus hojas cambió de versión
desde su última pasada correcta, repite el último resultado sin leer filas; corre igual cada
`force_seconds`, después de un error o si no se pudo leer la versión. No escribe en Smartsheet.
"""

import time
from collections.abc import Awaitable, Callable

from app.core.errors import AppError
from app.services.smartsheet import SmartsheetClient

Step = Callable[[], Awaitable[dict]]
# Una pasada del monitor dura pocos segundos: dentro de ella la versión se comparte.
_BOARD_MAX_AGE = 5.0


class VersionBoard:
    """Versión de cada hoja, compartida por los pasos de una misma pasada."""

    def __init__(
        self,
        client: SmartsheetClient | None,
        max_age: float = _BOARD_MAX_AGE,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client
        self.max_age = max_age
        self.clock = clock
        self._seen: dict[str, tuple[float, int]] = {}

    async def of(self, sheets: tuple[str, ...]) -> tuple[int, ...] | None:
        """Versiones de las hojas, en orden; None si alguna no se pudo leer (el paso corre)."""
        if self.client is None:
            return None
        found = []
        for sheet in sheets:
            version = await self._version(sheet)
            if version is None:
                return None
            found.append(version)
        return tuple(found)

    async def _version(self, sheet: str) -> int | None:
        now = self.clock()
        cached = self._seen.get(sheet)
        if cached and now - cached[0] < self.max_age:
            return cached[1]
        try:
            version = await self.client.sheet_version(sheet)
        except (AppError, KeyError, TypeError, ValueError):
            # Sin versión fiable el paso corre: saltarlo podría dejar un cambio sin copiar.
            return None
        self._seen[sheet] = (now, version)
        return version


class GatedStep:
    """Paso que sólo corre si cambió alguna de sus hojas o pasó `force_seconds`."""

    def __init__(
        self,
        step: Step,
        sheets: tuple[str, ...],
        board: VersionBoard,
        force_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.step = step
        self.sheets = tuple(sheet for sheet in sheets if sheet)
        self.board = board
        self.force_seconds = max(0.0, force_seconds)
        self.clock = clock
        self._versions: tuple[int, ...] | None = None
        self._last: dict | None = None
        self._ran_at: float | None = None

    async def run(self) -> dict:
        versions = await self.board.of(self.sheets)
        if self._can_skip(versions):
            return self._last or {}
        # Olvida las versiones hasta terminar bien: un error o una excepción obligan a correr.
        self._versions = None
        result = await self.step()
        if "error" not in result:
            # Las versiones de antes de correr: si el paso escribió, la pasada siguiente lo
            # vuelve a mirar una vez y ya no encuentra nada que hacer.
            self._versions, self._last, self._ran_at = versions, result, self.clock()
        return result

    def _can_skip(self, versions: tuple[int, ...] | None) -> bool:
        if versions is None or self._last is None or self._ran_at is None:
            return False
        if self.clock() - self._ran_at >= self.force_seconds:
            return False
        return versions == self._versions
