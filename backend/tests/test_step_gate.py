"""Saltar un paso cuando sus hojas no cambiaron (SPEC-B21 CA-03, CA-04, CA-B21-06); sin red."""

from unittest.mock import AsyncMock

import pytest

from app.core.errors import AppError
from app.services.step_gate import GatedStep, VersionBoard


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _client(versions: dict[str, int]) -> AsyncMock:
    client = AsyncMock()
    client.sheet_version.side_effect = lambda sheet: versions[sheet]
    return client


async def test_skips_while_no_sheet_changes_and_runs_on_a_change() -> None:
    clock, versions = Clock(), {"master": 1, "child": 5}
    board = VersionBoard(_client(versions), max_age=0, clock=clock)
    step = AsyncMock(return_value={"created": 1})
    gated = GatedStep(step, ("master", "child"), board, 600, clock=clock)
    assert await gated.run() == {"created": 1}
    clock.now += 30
    assert await gated.run() == {"created": 1}
    assert step.await_count == 1
    versions["child"] = 6
    await gated.run()
    assert step.await_count == 2


async def test_runs_after_an_error_after_the_forced_time_and_without_version() -> None:
    clock, versions = Clock(), {"master": 1}
    client = _client(versions)
    board = VersionBoard(client, max_age=0, clock=clock)
    step = AsyncMock(side_effect=[{"error": "x"}, {"ok": 1}, {"ok": 2}, {"ok": 3}])
    gated = GatedStep(step, ("master",), board, 600, clock=clock)
    await gated.run()
    await gated.run()
    assert step.await_count == 2  # con error no se recuerda
    clock.now += 600
    await gated.run()
    assert step.await_count == 3  # forzado
    client.sheet_version.side_effect = AppError("SMARTSHEET_UNAVAILABLE", "Sin respuesta.", 503)
    clock.now += 1
    await gated.run()
    assert step.await_count == 4  # sin versión, corre


async def test_an_exception_makes_the_next_pass_run() -> None:
    clock = Clock()
    board = VersionBoard(_client({"master": 1}), max_age=0, clock=clock)
    step = AsyncMock(side_effect=[{"ok": 1}, ValueError("falla"), {"ok": 2}])
    gated = GatedStep(step, ("master",), board, 600, clock=clock)
    await gated.run()
    clock.now += 600
    with pytest.raises(ValueError):
        await gated.run()
    clock.now += 1
    assert await gated.run() == {"ok": 2}


async def test_each_version_is_read_once_per_pass() -> None:
    clock = Clock()
    client = _client({"master": 1, "child": 2})
    board = VersionBoard(client, max_age=5, clock=clock)
    assert await board.of(("master", "child")) == (1, 2)
    await board.of(("master",))
    assert client.sheet_version.await_count == 2
    clock.now += 5
    await board.of(("master",))
    assert client.sheet_version.await_count == 3
    assert await VersionBoard(None).of(("master",)) is None
