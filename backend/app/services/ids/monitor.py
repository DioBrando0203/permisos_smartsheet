"""Procesador periódico opcional: simula por defecto; asigna sólo con coordinador autorizado."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import psycopg

from app.core.errors import AppError
from app.services.ids import pilot
from app.services.ids.cli import DSN
from app.services.ids.connector import IdConnector
from app.services.ids.preview import build_dry_run_report
from app.services.ids.processor import process_report
from app.services.smartsheet import SmartsheetClient

_LOCK = 714382002
# Resultados con escritura: pueden habilitar hijas, así que el siguiente ciclo va enseguida.
_WROTE = frozenset({"confirmed", "registered", "inherited", "rescoped", "detached", "followed"})


class IdMonitor:
    def __init__(
        self,
        client: SmartsheetClient,
        enabled: bool,
        interval: int,
        *,
        connector_factory: Callable[[], IdConnector] | None = None,
        max_rows: int = 5,
        dsn: str = DSN,
        after_cycle: Callable[[], Awaitable[dict]] | None = None,
        poll_seconds: float | None = None,
        obs_sync: Callable[[], Awaitable[dict]] | None = None,
        customer_change: bool = False,
        child_syncs: dict[str, Callable[[], Awaitable[dict]]] | None = None,
    ) -> None:
        self.client = client
        self.enabled = enabled
        self.interval = max(10, interval)
        self.connector_factory = connector_factory
        self.max_rows = max(1, max_rows)
        self.dsn = dsn
        # Paso opcional tras asignar (sincronizar el catálogo); sus fallos no afectan a los IDs.
        self.after_cycle = after_cycle
        # Entre ciclos se consulta la versión de la hoja; un cambio adelanta el ciclo (ID-43).
        self.poll_seconds = poll_seconds
        self.last_catalog: dict | None = None
        # Copia de conversaciones a Obs (SPEC-B17); aislada como el catálogo.
        self.obs_sync = obs_sync
        # Cambio de cliente y hijas al día (SPEC-ID01 ID-44 a ID-47); apagado por defecto.
        self.customer_change = customer_change
        self.last_obs: dict | None = None
        # Hojas hijas (SPEC-B18, SPEC-B19); cada una aislada como Obs.
        self.child_syncs = dict(child_syncs or {})
        self.last_children: dict[str, dict] = {}
        self.active = False
        self.last_run: str | None = None
        self.last_error: str | None = None
        self.last_counts: dict[str, int] = {}
        self.last_outcomes: dict[str, int] = {}
        self.last_results: list[dict] = []
        self.task: asyncio.Task | None = None

    @property
    def mode(self) -> str:
        """`assign` sólo si se construyó con todas las barreras de escritura activas."""
        return "assign" if self.connector_factory is not None else "simulation"

    def start(self) -> None:
        if self.enabled and (self.task is None or self.task.done()):
            self.task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def run_cycle(self) -> dict:
        """Un ciclo: DRY_RUN y, en modo asignación, procesamiento secuencial acotado."""
        report = await build_dry_run_report(
            self.client, self.dsn, customer_change=self.customer_change
        )
        results: list[dict] = []
        outcomes: dict[str, int] = {}
        if self.connector_factory is not None:
            outcomes = await process_report(
                self.connector_factory(), report, limit=self.max_rows, results=results
            )
            if self.after_cycle is not None:
                try:
                    self.last_catalog = await self.after_cycle()
                except Exception:
                    self.last_catalog = {"error": "catalog_sync_failed"}
            if self.obs_sync is not None:
                try:
                    self.last_obs = await self.obs_sync()
                except Exception as error:
                    self.last_obs = {"error": "obs_sync_failed", "type": type(error).__name__}
            for name, step in self.child_syncs.items():
                try:
                    self.last_children[name] = await step()
                except Exception as error:
                    failed = {"error": f"{name}_failed", "type": type(error).__name__}
                    self.last_children[name] = failed
        self.last_counts = report["counts"]
        self.last_outcomes = outcomes
        self.last_results = results
        self.last_error = None
        self.last_run = datetime.now(UTC).isoformat()
        return {
            "mode": self.mode,
            "counts": report["counts"],
            "outcomes": outcomes,
            "results": results,
        }

    async def run_once(self) -> dict:
        """Ciclo a demanda con el mismo bloqueo global: nunca se solapa con el periódico."""
        conn = await asyncio.to_thread(
            psycopg.connect, self.dsn, connect_timeout=5, autocommit=True
        )
        try:
            lock = await asyncio.to_thread(
                conn.execute, "SELECT pg_try_advisory_lock(%s)", (_LOCK,)
            )
            if not lock.fetchone()[0]:
                raise AppError("IDS_PROCESSOR_BUSY", "El procesador de IDs está en ejecución.", 409)
            return await self.run_cycle()
        finally:
            await asyncio.to_thread(conn.close)

    async def _wait(self, *, quick: bool) -> None:
        """Hasta `interval` segundos; un cambio en la hoja o una escritura acortan la espera."""
        if not self.poll_seconds:
            await asyncio.sleep(self.interval)
            return
        if quick:
            await asyncio.sleep(self.poll_seconds)
            return
        baseline = await self._versions()
        waited = 0.0
        while waited < self.interval:
            await asyncio.sleep(self.poll_seconds)
            waited += self.poll_seconds
            current = await self._versions()
            if baseline is None:
                baseline = current
            elif current is not None and current != baseline:
                return

    async def _versions(self) -> tuple[int, ...] | None:
        """Versión de cada hoja configurada; None si Smartsheet no responde (se espera más)."""
        try:
            return tuple([await self.client.sheet_version(item[0]) for item in pilot.SHEETS])
        except AppError:
            return None

    async def _run(self) -> None:
        conn = None
        try:
            conn = await asyncio.to_thread(
                psycopg.connect, self.dsn, connect_timeout=5, autocommit=True
            )
            lock = await asyncio.to_thread(
                conn.execute, "SELECT pg_try_advisory_lock(%s)", (_LOCK,)
            )
            if not lock.fetchone()[0]:
                self.last_error = "processor_already_active"
                return
            self.active = True
            while True:
                try:
                    await asyncio.to_thread(conn.execute, "SELECT 1")
                    await self.run_cycle()
                except psycopg.Error:
                    raise
                except Exception:
                    self.last_error = f"{self.mode}_failed"
                    self.last_run = datetime.now(UTC).isoformat()
                await self._wait(quick=bool(_WROTE & self.last_outcomes.keys()))
        except psycopg.Error:
            self.last_error = "database_unavailable"
        finally:
            self.active = False
            if conn:
                await asyncio.to_thread(conn.close)
