"""Freno y conteo de las llamadas a Smartsheet de un token (SPEC-B21 CA-02, RG-04).

El freno espera antes de enviar si en los últimos 60 s ya salieron `max_per_minute` llamadas:
así el servicio no llega al 429 de Smartsheet (300 por minuto por token). El conteo resume
llamadas por minuto, 429 y esperas para `/api/ids/logs`. No envía nada: lo usa el transporte.
"""

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

_WINDOW = 60.0
_HOUR_BUCKETS = 60


@dataclass(frozen=True)
class UsageSnapshot:
    last_minute: int
    last_hour: int
    total: int
    rate_limited: int
    throttled: int
    max_per_minute: int


class ApiUsage:
    """Ventana deslizante de 60 s para el freno y cubetas por minuto para el resumen."""

    def __init__(
        self,
        max_per_minute: int,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.max_per_minute = max(1, max_per_minute)
        self._clock = clock
        self._sleep = sleep
        self._sent: deque[float] = deque()
        self._minutes: dict[int, int] = {}
        self._lock = asyncio.Lock()
        self.total = self.rate_limited = self.throttled = 0

    async def acquire(self) -> None:
        """Reserva un lugar en la ventana; si está llena, espera a que se libere uno."""
        async with self._lock:
            while True:
                now = self._clock()
                while self._sent and now - self._sent[0] >= _WINDOW:
                    self._sent.popleft()
                if len(self._sent) < self.max_per_minute:
                    break
                self.throttled += 1
                await self._sleep(_WINDOW - (now - self._sent[0]))
            self._sent.append(now)
            self._count(now)

    def record_status(self, status: int) -> None:
        if status == 429:
            self.rate_limited += 1

    def snapshot(self) -> UsageSnapshot:
        now = self._clock()
        minute = int(now // _WINDOW)
        hour = sum(n for m, n in self._minutes.items() if minute - m < _HOUR_BUCKETS)
        return UsageSnapshot(
            last_minute=sum(1 for sent in self._sent if now - sent < _WINDOW),
            last_hour=hour,
            total=self.total,
            rate_limited=self.rate_limited,
            throttled=self.throttled,
            max_per_minute=self.max_per_minute,
        )

    def _count(self, now: float) -> None:
        minute = int(now // _WINDOW)
        self._minutes[minute] = self._minutes.get(minute, 0) + 1
        self.total += 1
        for old in [m for m in self._minutes if minute - m >= _HOUR_BUCKETS]:
            del self._minutes[old]
