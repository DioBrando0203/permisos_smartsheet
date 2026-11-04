"""Procesador periódico opcional: simula por defecto; asigna sólo con coordinador autorizado."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import psycopg

from app.core.errors import AppError
from app.services.ids.cli import DSN
from app.services.ids.connector import IdConnector
from app.services.ids.preview import build_dry_run_report
from app.services.ids.processor import process_report
from app.services.smartsheet import SmartsheetClient

_LOCK = 714382002


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
    ) -> None:
        self.client = client
        self.enabled = enabled
        self.interval = max(10, interval)
        self.connector_factory = connector_factory
        self.max_rows = max(1, max_rows)
        self.dsn = dsn
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
        report = await build_dry_run_report(self.client, self.dsn)
        results: list[dict] = []
        outcomes: dict[str, int] = {}
        if self.connector_factory is not None:
            outcomes = await process_report(
                self.connector_factory(), report, limit=self.max_rows, results=results
            )
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
                await asyncio.sleep(self.interval)
        except psycopg.Error:
            self.last_error = "database_unavailable"
        finally:
            self.active = False
            if conn:
                await asyncio.to_thread(conn.close)
