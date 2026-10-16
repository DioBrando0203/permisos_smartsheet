"""Único punto que habla con la API 2.0 de Smartsheet (Gateway, SM-02).

Autentica, acota la concurrencia, reintenta con espera exponencial, pagina y traduce errores.
No conoce FastAPI ni el contrato HTTP del panel; devuelve dataclasses `Raw*`.
"""

import asyncio
import logging
import random
import time
from typing import Any

import httpx

from app.core.config import Settings
from app.services.smartsheet import mappers
from app.services.smartsheet.errors import token_missing, translate_error, unavailable
from app.services.smartsheet.types import (
    NewShare,
    RawCellChange,
    RawColumn,
    RawContact,
    RawGroup,
    RawMe,
    RawRow,
    RawShare,
    RawSheet,
    RawUser,
    ShareMessage,
)

logger = logging.getLogger("app.smartsheet")

SHARES_PATH = "/shares"
_READ_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
# Ante 500 una escritura pudo aplicarse; reintentarla duplicaría permisos o correos (SM-04).
_WRITE_RETRY_STATUS = frozenset({429, 503})
_MAX_BACKOFF_SECONDS = 30.0
_SHARING_INCLUDE = "ITEM,WORKSPACE"
# Máximo de filas por página que admite Smartsheet al leer una hoja.
_ROWS_PAGE = 500


class SmartsheetClient:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._http = http or httpx.AsyncClient(
            base_url=settings.smartsheet_base_url,
            timeout=settings.smartsheet_timeout_seconds,
        )
        self._semaphore = asyncio.Semaphore(settings.smartsheet_max_concurrency)

    async def aclose(self) -> None:
        await self._http.aclose()

    # Lecturas

    async def get_me(self) -> RawMe:
        return mappers.to_me(await self._request("GET", "/users/me"))

    async def list_sheets(self) -> list[RawSheet]:
        return [mappers.to_sheet(item) for item in await self._get_all("/sheets")]

    async def get_sheet_access_level(self, sheet_id: str) -> RawSheet:
        """Lee la hoja sin filas: sólo para conocer el nivel actual del token (SM-06)."""
        params = {"pageSize": 1, "page": 1, "exclude": "nonexistentCells"}
        data = await self._request("GET", f"/sheets/{sheet_id}", params=params)
        return mappers.to_sheet(data)

    async def list_sheet_shares(self, sheet_id: str) -> list[RawShare]:
        params = _asset(sheet_id) | {"sharingInclude": _SHARING_INCLUDE}
        return [mappers.to_share(item) for item in await self._get_items(SHARES_PATH, params)]

    async def get_sheet_share(self, sheet_id: str, share_id: str) -> RawShare:
        data = await self._request("GET", f"{SHARES_PATH}/{share_id}", params=_asset(sheet_id))
        return mappers.to_share(data)

    async def list_users(self) -> list[RawUser]:
        return [mappers.to_user(item) for item in await self._get_all("/users")]

    async def list_groups(self) -> list[RawGroup]:
        return [mappers.to_group(item) for item in await self._get_all("/groups")]

    async def list_contacts(self) -> list[RawContact]:
        return [mappers.to_contact(item) for item in await self._get_all("/contacts")]

    async def list_columns(self, sheet_id: str) -> list[RawColumn]:
        items = await self._get_all(f"/sheets/{sheet_id}/columns")
        return [mappers.to_column(item) for item in items]

    async def list_rows_with_authors(self, sheet_id: str, label_column_id: str) -> list[RawRow]:
        """Todas las filas con quién las creó y modificó; sólo la columna de etiqueta."""
        rows: list[RawRow] = []
        page = 1
        while True:
            params = {
                "include": "writerInfo",
                "columnIds": label_column_id,
                "pageSize": _ROWS_PAGE,
                "page": page,
            }
            data = await self._request("GET", f"/sheets/{sheet_id}", params=params)
            batch = data.get("rows", [])
            rows.extend(mappers.to_row(item) for item in batch)
            # Smartsheet repite la última página si se pide una mayor: cortar por total.
            if len(batch) < _ROWS_PAGE or len(rows) >= int(data.get("totalRowCount") or 0):
                return rows
            page += 1

    async def get_row_filled_columns(self, sheet_id: str, row_id: str) -> list[str]:
        """Columnas con valor en una fila: las que tienen historial que mostrar."""
        data = await self._request("GET", f"/sheets/{sheet_id}/rows/{row_id}")
        return [
            str(cell["columnId"])
            for cell in data.get("cells", [])
            if cell.get("value") is not None or cell.get("displayValue")
        ]

    async def get_cell_history(
        self, sheet_id: str, row_id: str, column_id: str
    ) -> list[RawCellChange]:
        path = f"/sheets/{sheet_id}/rows/{row_id}/columns/{column_id}/history"
        return [mappers.to_cell_change(item) for item in await self._get_all(path)]

    # Escrituras (bloqueadas antes de llegar aquí en modo solo lectura)

    async def create_sheet_shares(
        self, sheet_id: str, shares: list[NewShare], message: ShareMessage | None
    ) -> None:
        params = _asset(sheet_id) | {"sendEmail": "true" if message else "false"}
        body = [_share_body(share, message) for share in shares]
        await self._request("POST", SHARES_PATH, params=params, json=body)

    async def update_sheet_share(self, sheet_id: str, share_id: str, level: str) -> None:
        path = f"{SHARES_PATH}/{share_id}"
        await self._request("PATCH", path, params=_asset(sheet_id), json={"accessLevel": level})

    async def delete_sheet_share(self, sheet_id: str, share_id: str) -> None:
        await self._request("DELETE", f"{SHARES_PATH}/{share_id}", params=_asset(sheet_id))

    # Transporte

    async def _get_all(self, path: str) -> list[dict[str, Any]]:
        """Endpoints clásicos: `includeAll=true` y, si aun así hay más páginas, por `page`."""
        data = await self._request("GET", path, params={"includeAll": "true"})
        items = list(data.get("data", []))
        for page in range(2, int(data.get("totalPages") or 1) + 1):
            more = await self._request("GET", path, params={"includeAll": "true", "page": page})
            items.extend(more.get("data", []))
        return items

    async def _get_items(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Endpoints nuevos (`/shares`): siguen `lastKey` hasta el final."""
        items: list[dict[str, Any]] = []
        last_key: str | None = None
        while True:
            page_params = params | ({"lastKey": last_key} if last_key else {})
            data = await self._request("GET", path, params=page_params)
            items.extend(data.get("items", []))
            last_key = data.get("lastKey")
            if not last_key:
                return items

    async def _request(
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


def _asset(sheet_id: str) -> dict[str, str]:
    return {"assetType": "sheet", "assetId": sheet_id}


def _share_body(share: NewShare, message: ShareMessage | None) -> dict[str, Any]:
    body: dict[str, Any] = {"accessLevel": str(share.access_level)}
    if share.email:
        body["email"] = share.email
    if share.group_id:
        body["groupId"] = int(share.group_id)
    if message and message.subject:
        body["subject"] = message.subject
    if message and message.message:
        body["message"] = message.message
    return body
