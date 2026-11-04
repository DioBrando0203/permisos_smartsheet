"""Procesador opcional de simulación; nunca reserva ni escribe en Smartsheet."""

import asyncio
from datetime import UTC, datetime

import psycopg

from app.services.ids.cli import DSN
from app.services.ids.preview import build_dry_run_report
from app.services.smartsheet import SmartsheetClient

_LOCK = 714382002


class IdMonitor:
    def __init__(self, client: SmartsheetClient, enabled: bool, interval: int) -> None:
        self.client = client
        self.enabled = enabled
        self.interval = max(10, interval)
        self.active = False
        self.last_run: str | None = None
        self.last_error: str | None = None
        self.last_counts: dict[str, int] = {}
        self.task: asyncio.Task | None = None

    def start(self) -> None:
        if self.enabled and (self.task is None or self.task.done()):
            self.task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def _run(self) -> None:
        conn = None
        try:
            conn = await asyncio.to_thread(psycopg.connect, DSN, connect_timeout=5, autocommit=True)
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
                    report = await build_dry_run_report(self.client, DSN)
                    self.last_counts = report["counts"]
                    self.last_error = None
                except psycopg.Error:
                    raise
                except Exception:
                    self.last_error = "simulation_failed"
                self.last_run = datetime.now(UTC).isoformat()
                await asyncio.sleep(self.interval)
        except psycopg.Error:
            self.last_error = "database_unavailable"
        finally:
            self.active = False
            if conn:
                await asyncio.to_thread(conn.close)
