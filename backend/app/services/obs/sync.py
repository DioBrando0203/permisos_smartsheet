"""Copia los comentarios nuevos de cada fila a la columna Obs (SPEC-B17): agrega, nunca borra.

Lee los de la maestra y los de las hojas de equipo que son su reflejo (OB-17, `sources.py`);
todos se componen juntos en el `Obs` de su fila de la maestra.
"""

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
from app.services.obs.sources import Entry, MasterRows, MirrorRows, Source, mirror_sheets
from app.services.obs.store import ObsStore
from app.services.smartsheet import SmartsheetClient
from app.services.smartsheet.types import RawComment
from app.services.step_gate import GatedStep, VersionBoard

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


def by_target(entries: list[Entry]) -> dict[str, list[Entry]]:
    """Comentarios por fila de la maestra; primero la fila con el comentario más antiguo."""
    rows: dict[str, list[Entry]] = {}
    for entry in entries:
        rows.setdefault(entry.target, []).append(entry)
    oldest = {row: min(e.comment.created_at for e in items) for row, items in rows.items()}  # type: ignore[type-var]
    return {row: rows[row] for row in sorted(rows, key=lambda row: oldest[row])}


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
        mirrors: tuple[str, ...] = (),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.client = client
        self.store = store
        self.mirrors = mirrors
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
        entries = await self._entries(MasterRows(sheet))
        for source in self._mirrors(sheet):
            try:
                entries += await self._mirror_entries(source)
            except (AppError, ValueError) as error:
                # Bulkhead: una hoja de equipo con problemas no frena el Obs de la maestra.
                logger.warning("obs: hoja %s sin leer (%s)", source.sheet, type(error).__name__)
                counts["errors"] += 1
        if entries:
            # La API sigue listando conversaciones de filas borradas: sólo filas vigentes (OB-14).
            existing = {row.id for row in await self.client.list_rows(sheet, [column])}
            entries = [entry for entry in entries if entry.target in existing]
        pending = by_target(entries)
        counts["waiting_rows"] += max(0, len(pending) - self.max_rows)
        for row_id, items in list(pending.items())[: self.max_rows]:
            await self._row(sheet, column, row_id, items, counts)

    def _mirrors(self, sheet: str) -> list[MirrorRows]:
        """Las hojas de equipo son reflejo de la maestra principal, no de otras hojas."""
        return [MirrorRows(mirror) for mirror in self.mirrors] if sheet == pilot.PRESENTABLE else []

    async def _mirror_entries(self, source: MirrorRows) -> list[Entry]:
        if await self.client.sheet_workspace_id(source.sheet) != PILOT_WORKSPACE:
            raise ValueError("La hoja no pertenece al workspace Pruebas")
        return await self._entries(source)

    async def _entries(self, source: Source) -> list[Entry]:
        """Comentarios nuevos de la hoja, cada uno con la fila de la maestra que lo recibe."""
        comments = await self.client.list_row_comments(source.sheet)
        done = await asyncio.to_thread(self.store.processed, source.sheet)
        pending = pending_by_row(comments, done)
        if not pending:
            return []
        owners = await source.owners(self.client, set(pending))
        return [
            Entry(source.sheet, owners[row], item)
            for row, items in pending.items()
            if row in owners
            for item in items
        ]

    async def _column(self, sheet: str) -> str:
        title = self.settings.app_obs_column
        matches = [item.id for item in await self.client.list_columns(sheet) if item.title == title]
        if len(matches) != 1:
            raise ValueError("Columna Obs no encontrada o duplicada")
        return matches[0]

    async def _row(
        self, sheet: str, column: str, row_id: str, items: list[Entry], counts: dict[str, int]
    ) -> None:
        try:
            current = (await self.client.get_row(sheet, row_id)).cells.get(column)
            comments = [entry.comment for entry in items]
            value, archived = rules.fit(rules.compose(current, comments, self.zone))
            # Cada comentario queda registrado en la hoja y la fila donde está (OB-05).
            done = [(entry.sheet, entry.comment.row_id, entry.comment.id) for entry in items]
            if archived:
                # Primero el archivo: si después falla Obs, el texto ya está a salvo (OB-07).
                created = await self._archive(sheet, row_id, archived)
                done.extend((sheet, row_id, comment) for comment in created)
                counts["archived"] += 1
        except AppError as error:
            logger.warning("obs: fila %s sin procesar (%s)", row_id, error.code)
            counts["errors"] += 1
            return
        if not await self._write(sheet, column, row_id, value):
            counts["errors"] += 1
            return
        await asyncio.to_thread(self.store.record, done)
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
    settings: Settings,
    client: SmartsheetClient,
    dsn: str = DSN,
    board: VersionBoard | None = None,
) -> Callable[[], Awaitable[dict]] | None:
    """Paso del procesador; None si está apagado o faltan barreras de escritura (OB-10).

    Se salta si la hoja no cambió, pero corre al menos cada `app_obs_force_seconds`: una
    conversación nueva quizá no cambie la versión de la hoja (SPEC-B21 CA-04).
    """
    if not settings.app_obs_sync_enabled or not writes_allowed(settings):
        return None
    mirrors = mirror_sheets(settings)
    sync = ObsSync(
        settings,
        client,
        ObsStore(dsn),
        zone=ZoneInfo(settings.app_obs_timezone),
        interval=settings.app_obs_interval_seconds,
        max_rows=settings.app_obs_max_rows,
        mirrors=mirrors,
    )
    sheets = (*(item[0] for item in pilot.SHEETS), *mirrors)
    board = board or VersionBoard(client)
    return GatedStep(sync.run, sheets, board, settings.app_obs_force_seconds).run
