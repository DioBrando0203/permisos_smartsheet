"""Freno y conteo de llamadas a Smartsheet (SPEC-B21 CA-02, RG-04, CA-B21-05); sin red."""

import httpx
import respx

from app.services.smartsheet import SmartsheetClient
from app.services.smartsheet.usage import ApiUsage
from tests.conftest import BASE, make_settings


class FakeTime:
    """Reloj y espera simulados: esperar adelanta el reloj."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def clock(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


async def test_waits_when_the_minute_is_full_and_counts_it() -> None:
    time = FakeTime()
    usage = ApiUsage(3, clock=time.clock, sleep=time.sleep)
    for _ in range(3):
        await usage.acquire()
        time.now += 1
    await usage.acquire()
    assert time.slept == [57.0]  # el primero salió en 1000: se libera en 1060
    usage.record_status(429)
    snap = usage.snapshot()
    assert (snap.total, snap.throttled, snap.rate_limited) == (4, 1, 1)
    assert snap.last_minute == 3 and snap.last_hour == 4 and snap.max_per_minute == 3


async def test_the_client_counts_every_attempt_and_each_429() -> None:
    client = SmartsheetClient(make_settings())
    try:
        with respx.mock(base_url=BASE) as router:
            router.get("/users/me").mock(
                side_effect=[
                    httpx.Response(429, json={"errorCode": 4003}),
                    httpx.Response(200, json={"id": 1, "email": "persona1@example.com"}),
                ]
            )
            await client.get_me()
        usage = client.api_usage()
    finally:
        await client.aclose()
    assert usage.total == 2 and usage.rate_limited == 1 and usage.throttled == 0
