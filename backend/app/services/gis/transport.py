"""Transporte para GIS público: sin autenticación ni vínculo con Smartsheet."""

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class GisFailure(Exception):
    status: str


class GisTransport:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._timeout = settings.gis_timeout_seconds
        self._retries = settings.gis_max_retries
        self._http = http or httpx.AsyncClient(timeout=self._timeout)
        self._semaphore = asyncio.Semaphore(settings.gis_max_concurrency)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get(self, url: str, params: dict[str, str]) -> tuple[dict[str, Any], float]:
        """Lee ArcGIS con reintentos de red/5xx; nunca transmite credenciales."""
        started = time.perf_counter()
        for attempt in range(self._retries + 1):
            try:
                async with self._semaphore:
                    response = await self._http.get(url, params=params)
            except httpx.TimeoutException:
                if attempt == self._retries:
                    raise GisFailure("timeout") from None
                continue
            except httpx.TransportError:
                if attempt == self._retries:
                    raise GisFailure("error") from None
                continue
            if response.status_code >= 500 and attempt < self._retries:
                continue
            if response.status_code >= 400:
                raise GisFailure("error")
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                raise GisFailure("error")
            return data, round((time.perf_counter() - started) * 1000, 1)
        raise GisFailure("error")
