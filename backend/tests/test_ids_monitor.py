"""Monitor del procesador: fallos en el registro y consulta lenta sin cambios (SPEC-B21).

CA-B21-03 y CA-B21-07; sin red ni PostgreSQL.
"""

import logging
from unittest.mock import AsyncMock, Mock

import app.services.ids.monitor as module

EMPTY = {"counts": {}, "pending_or_conflicting_rows": []}


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def test_failed_step_is_logged(monkeypatch, caplog) -> None:
    monkeypatch.setattr(module, "build_dry_run_report", AsyncMock(return_value=EMPTY))
    monkeypatch.setattr(module, "process_report", AsyncMock(return_value={}))

    async def broken() -> dict:
        raise ValueError("falla sintética")

    monitor = module.IdMonitor(
        AsyncMock(), True, 60, connector_factory=Mock(), child_syncs={"records": broken}
    )
    caplog.set_level(logging.ERROR)
    await monitor.run_cycle()
    assert monitor.last_children["records"] == {"error": "records_failed", "type": "ValueError"}
    assert "ciclo: falló el paso records" in caplog.text
    assert "ValueError: falla sintética" in caplog.text


async def test_monitor_polls_slower_when_idle(monkeypatch) -> None:
    clock, slept = Clock(), []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        clock.now += seconds

    monkeypatch.setattr(module.asyncio, "sleep", fake_sleep)
    client = AsyncMock()
    client.sheet_version.return_value = 7
    idle = module.IdlePolling(after=120, poll_seconds=30)
    monitor = module.IdMonitor(client, True, 60, poll_seconds=5, idle=idle, clock=clock)
    await monitor._wait(quick=False)
    await monitor._wait(quick=False)
    assert slept == [5] * 24  # los primeros 120 s sin cambios, consulta rápida
    slept.clear()
    await monitor._wait(quick=False)
    assert slept == [30, 30]  # quieta: consulta lenta
    versions = iter([7, 7, 8])
    client.sheet_version.side_effect = lambda _sheet: next(versions)
    slept.clear()
    await monitor._wait(quick=False)  # cambia en la segunda consulta y vuelve a la rápida
    assert slept == [30, 30] and monitor._poll_step() == 5
