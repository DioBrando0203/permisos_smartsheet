"""Transporte HTTP hacia la API 2.0 de Smartsheet: autenticación, reintentos y paginación.

Lo usa sólo `SmartsheetClient` (SM-02). Traduce errores a `AppError` y nunca registra el token,
cuerpos ni correos.
"""

import asyncio
import logging
import random
import time
from typing import Any

import httpx

from app.core.config import Settings
from app.services.smartsheet.errors import token_missing, translate_error, unavailable

logger = logging.getLogger("app.smartsheet")

_READ_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
# Ante 500 una escritura pudo aplicarse; reintentarla duplicaría permisos o correos (SM-04).
_WRITE_RETRY_STATUS = frozenset({429, 503})
_MAX_BACKOFF_SECONDS = 30.0
# Tamaño de página de los listados; 100 lo aceptan todos los endpoints verificados.
_PAGE_SIZE = 100
# Tope de seguridad: evita un ciclo infinito si Smartsheet repite páginas completas.
_MAX_PAGES = 1000


class Transport:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._http = http or httpx.AsyncClient(
            base_url=settings.smartsheet_base_url,
            timeout=settings.smartsheet_timeout_seconds,
        )
        self._semaphore = asyncio.Semaphore(settings.smartsheet_max_concurrency)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get_all(
        self, path: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Endpoints clásicos con paginación explícita (`page`, `pageSize`).

        No usa `includeAll`: Smartsheet ya lo retiró en algunos endpoints (B-09). Corta cuando
        llega una página incompleta, cuando Smartsheet devuelve otra página que la pedida
        (`/sheets` repite la última, `/users/sheets` responde `pageNumber` 0) o al llegar a
        `totalPages`, que puede venir como -1 (B-06).
        """
        items: list[dict[str, Any]] = []
        for page in range(1, _MAX_PAGES + 1):
            page_params = (params or {}) | {"pageSize": _PAGE_SIZE, "page": page}
            data = await self.request("GET", path, params=page_params)
            batch = data.get("data", [])
            if int(data.get("pageNumber") or page) != page:
                return items
            items.extend(batch)
            total_pages = int(data.get("totalPages") or 0)
            if len(batch) < _PAGE_SIZE or 0 < total_pages <= page:
                return items
        logger.warning("smartsheet GET %s -> corte en %d páginas", path, _MAX_PAGES)
        return items

    async def get_items(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Endpoints nuevos (`/shares`): siguen `lastKey` hasta el final."""
        items: list[dict[str, Any]] = []
        last_key: str | None = None
        while True:
            page_params = params | ({"lastKey": last_key} if last_key else {})
            data = await self.request("GET", path, params=page_params)
            items.extend(data.get("items", []))
            last_key = data.get("lastKey")
            if not last_key:
                return items

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        if not self._settings.has_token:
            raise token_missing()
        retry_status = _READ_RETRY_STATUS if method == "GET" else _WRITE_RETRY_STATUS
        attempts = self._settings.smartsheet_max_retries + 1
        for attempt in range(attempts):
            is_last = attempt == attempts - 1
            response = await self._send(method, path, params, json, can_retry=not is_last)
            if response is None:
                await self._wait(attempt, None)
                continue
            if response.status_code < 400:
                return response.json() if response.content else {}
            if response.status_code in retry_status and not is_last:
                await self._wait(attempt, response.headers.get("Retry-After"))
                continue
            raise translate_error(response)
        raise unavailable()

    async def _send(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None,
        json: Any,
        *,
        can_retry: bool,
    ) -> httpx.Response | None:
        """Envía una vez. `None` significa error de red reintentable (sólo en lecturas)."""
        started = time.perf_counter()
        try:
            async with self._semaphore:
                response = await self._http.request(
                    method, path, params=params, json=json, headers=self._auth_header()
                )
        except httpx.TransportError:
            logger.warning("smartsheet %s %s -> error de red", method, path)
            if method == "GET" and can_retry:
                return None
            raise unavailable() from None
        elapsed_ms = (time.perf_counter() - started) * 1000
        # Sólo método, ruta sin query, estado y duración: nunca token, cuerpos ni correos.
        logger.info(
            "smartsheet %s %s -> %s (%.0f ms)", method, path, response.status_code, elapsed_ms
        )
        return response

    def _auth_header(self) -> dict[str, str]:
        token = self._settings.smartsheet_access_token
        assert token is not None
        return {"Authorization": f"Bearer {token.get_secret_value()}"}

    async def _wait(self, attempt: int, retry_after: str | None) -> None:
        base = self._settings.smartsheet_retry_base_seconds
        delay = min(base * (2**attempt), _MAX_BACKOFF_SECONDS) * random.uniform(0.75, 1.25)
        if retry_after and retry_after.isdigit():
            delay = max(delay, float(retry_after))
        await asyncio.sleep(delay if base > 0 else 0)
