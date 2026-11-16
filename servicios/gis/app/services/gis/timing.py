"""Mide una consulta a una fuente GIS y la vuelve `SourceStatus` sin tumbar la respuesta."""

from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import TypeVar

from app.models.map import SourceStatus
from app.services.gis.transport import GisFailure

T = TypeVar("T")


async def run_source(
    source: str, load: Callable[[], Awaitable[T]], empty: T
) -> tuple[T, SourceStatus]:
    """Lo que devolvió la fuente, o `empty` si falló, con su estado y duración."""
    started = perf_counter()
    try:
        found, status = await load(), "ok"
    except GisFailure as error:
        found, status = empty, error.status
    elapsed = round((perf_counter() - started) * 1000, 1)
    return found, SourceStatus(id=source, status=status, ms=elapsed)
