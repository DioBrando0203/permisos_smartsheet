"""Copia los comentarios nuevos de cada fila a la columna Obs (SPEC-B17): agrega, nunca borra."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, tzinfo
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.core.errors import AppError
from app.services.ids import pilot
from app.services.ids.cli import DSN
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.runtime import writes_allowed
from app.services.obs import rules
from app.services.obs.store import ObsStore
from app.services.smartsheet import SmartsheetClient
from app.services.smartsheet.types import RawComment

logger = logging.getLogger(__name__)


def pending_by_row(comments: list[RawComment], done: set[str]) -> dict[str, list[RawComment]]:
    """Comentarios por copiar agrupados por fila; primero la fila con el comentario más antiguo."""
    rows: dict[str, list[RawComment]] = {}
    for item in comments:
        if item.id in done or item.created_at is None or rules.is_skipped(item.text):
            continue
        rows.setdefault(item.row_id, []).append(item)
    oldest = {row: min(item.created_at for item in items) for row, items in rows.items()}
    return {row: rows[row] for row in sorted(rows, key=lambda row: oldest[row])}  # type: ignore[arg-type,return-value]


class ObsSync:
    def __init__(
        self,
        settings: Settings,
        client: SmartsheetClient,
        store: ObsStore,
        *,
        zone: tzinfo,
        interval: float = 30.0,
        max_rows: int = 20,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.client = client
        self.store = store
        self.zone = zone
        self.interval = max(0.0, interval)
        self.max_rows = max(1, max_rows)
        self.clock = clock
        self.last: dict | None = None
        self._last_at: float | None = None

    async def run(self) -> dict:
        """Una pasada por hoja configurada; entre pasadas espera al menos `interval` (OB-12)."""
        now = self.clock()
        if self.last is not None and self._last_at is not None:
            if now - self._last_at < self.interval:
                return self.last
        self._last_at = now
        counts = {"rows": 0, "comments": 0, "archived": 0, "waiting_rows": 0, "errors": 0}
        for sheet in [item[0] for item in pilot.SHEETS]:
            await self._sheet(sheet, counts)
        self.last = counts
        return counts

    async def _sheet(self, sheet: str, counts: dict[str, int]) -> None:
        if not writes_allowed(self.settings):
            raise ValueError("Escritura deshabilitada por las barreras del servicio")
        if await self.client.sheet_workspace_id(sheet) != PILOT_WORKSPACE:
            raise ValueError("La hoja no pertenece al workspace Pruebas")
        column = await self._column(sheet)
        comments = await self.client.list_row_comments(sheet)
        done = await asyncio.to_thread(self.store.processed, sheet)
        pending = pending_by_row(comments, done)
        if pending:
            # La API sigue listando conversaciones de filas borradas: sólo filas vigentes (OB-14).
            existing = {row.id for row in await self.client.list_rows(sheet, [column])}
            pending = {row: items for row, items in pending.items() if row in existing}
        counts["waiting_rows"] += max(0, len(pending) - self.max_rows)
        for row_id, items in list(pending.items())[: self.max_rows]:
            await self._row(sheet, column, row_id, items, counts)

    async def _column(self, sheet: str) -> str:
        title = self.settings.app_obs_column
        matches = [item.id for item in await self.client.list_columns(sheet) if item.title == title]
        if len(matches) != 1:
            raise ValueError("Columna Obs no encontrada o duplicada")
        return matches[0]

    async def _row(
        self, sheet: str, column: str, row_id: str, items: list[RawComment], counts: dict[str, int]
    ) -> None:
        try:
            current = (await self.client.get_row(sheet, row_id)).cells.get(column)
            value, archived = rules.fit(rules.compose(current, items, self.zone))
            ids = [item.id for item in items]
            if archived:
                # Primero el archivo: si después falla Obs, el texto ya está a salvo (OB-07).
                ids.extend(await self._archive(sheet, row_id, archived))
                counts["archived"] += 1
        except AppError as error:
            logger.warning("obs: fila %s sin procesar (%s)", row_id, error.code)
            counts["errors"] += 1
            return
        if not await self._write(sheet, column, row_id, value):
            counts["errors"] += 1
            return
        await asyncio.to_thread(self.store.record, sheet, row_id, ids)
        counts["rows"] += 1
        counts["comments"] += len(items)

    async def _archive(self, sheet: str, row_id: str, archived: str) -> list[str]:
        stamp = datetime.now(UTC).astimezone(self.zone).strftime("%m.%d.%Y")
        created = []
        for text in rules.archive_comments(archived, stamp):
            comment = await self.client.add_row_comment(sheet, row_id, text)
            if comment is not None:
                created.append(comment)
        return created

    async def _write(self, sheet: str, column: str, row_id: str, value: str) -> bool:
        """True si Obs quedó con el valor; ante error del servidor se relee la fila (OB-08)."""
        try:
            await self.client.update_row_text(sheet, row_id, column, value)
            return True
        except AppError as error:
            if error.status < 500:
                logger.warning("obs: escritura rechazada en fila %s (%s)", row_id, error.code)
                return False
        try:
            reread = await self.client.get_row(sheet, row_id)
        except AppError:
            return False
        return (reread.cells.get(column) or "") == value.strip()


def obs_hook(
    settings: Settings, client: SmartsheetClient, dsn: str = DSN
) -> Callable[[], Awaitable[dict]] | None:
    """Paso del procesador; None si está apagado o faltan barreras de escritura (OB-10)."""
    if not settings.app_obs_sync_enabled or not writes_allowed(settings):
        return None
    sync = ObsSync(
        settings,
        client,
        ObsStore(dsn),
        zone=ZoneInfo(settings.app_obs_timezone),
        interval=settings.app_obs_interval_seconds,
        max_rows=settings.app_obs_max_rows,
    )
    return sync.run
