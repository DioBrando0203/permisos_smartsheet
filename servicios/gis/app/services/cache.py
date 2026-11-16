"""Caché en memoria con vencimiento, invalidación y una sola carga por clave (ADR-B06).

Vive en `app.state` (no a nivel de módulo) para que cada prueba tenga la suya.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class _Entry:
    value: Any
    expires_at: float
    loaded_at: datetime


class TtlCache:
    def __init__(self, ttl_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._entries: dict[str, _Entry] = {}
        self._inflight: dict[str, asyncio.Task[Any]] = {}

    async def get_or_load(
        self, key: str, loader: Callable[[], Awaitable[T]], *, refresh: bool = False
    ) -> T:
        """Devuelve el valor vigente o lo carga; cargas simultáneas comparten una llamada."""
        entry = self._entries.get(key)
        if entry and not refresh and entry.expires_at > self._clock():
            return entry.value
        task = self._inflight.get(key)
        if task is None:
            task = asyncio.ensure_future(self._load(key, loader))
            self._inflight[key] = task
        return await asyncio.shield(task)

    def loaded_at(self, key: str) -> datetime | None:
        entry = self._entries.get(key)
        return entry.loaded_at if entry else None

    def invalidate(self, key: str) -> None:
        self._entries.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        for key in [key for key in self._entries if key.startswith(prefix)]:
            del self._entries[key]

    async def _load(self, key: str, loader: Callable[[], Awaitable[T]]) -> T:
        try:
            value = await loader()
            now = datetime.now(UTC)
            self._entries[key] = _Entry(value, self._clock() + self._ttl, now)
            return value
        finally:
            self._inflight.pop(key, None)
