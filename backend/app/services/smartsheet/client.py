"""Único punto que habla con la API 2.0 de Smartsheet (Gateway, SM-02).

Cada método es un recurso de Smartsheet mapeado a dataclasses `Raw*`; el transporte (auth,
reintentos, paginación) vive en `transport.py`. No conoce FastAPI ni el contrato del panel.
"""

from typing import Any

import httpx

from app.core.config import Settings
from app.services.smartsheet import mappers
from app.services.smartsheet.transport import Transport
from app.services.smartsheet.types import (
    NewShare,
    RawAutomation,
    RawCellChange,
    RawColumn,
    RawComment,
    RawContact,
    RawGroup,
    RawMe,
    RawRow,
    RawShare,
    RawSheet,
    RawUser,
    ShareMessage,
)

SHARES_PATH = "/shares"
_SHARING_INCLUDE = "ITEM,WORKSPACE"
# Máximo de filas por página que admite Smartsheet al leer una hoja.
_ROWS_PAGE = 500


class SmartsheetClient:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._transport = Transport(settings, http)

    async def aclose(self) -> None:
        await self._transport.aclose()

    # Lecturas

    async def get_me(self) -> RawMe:
        return mappers.to_me(await self._transport.request("GET", "/users/me"))

    async def list_sheets(self) -> list[RawSheet]:
        return [mappers.to_sheet(item) for item in await self._transport.get_all("/sheets")]

    async def list_org_sheets(self) -> list[RawSheet]:
        """Hojas de toda la organización (sólo administrador del sistema)."""
        return [
            mappers.to_org_sheet(item) for item in await self._transport.get_all("/users/sheets")
        ]

    async def get_sheet_access_level(self, sheet_id: str) -> RawSheet:
        """Lee la hoja sin filas: sólo para conocer el nivel actual del token (SM-06)."""
        params = {"pageSize": 1, "page": 1, "exclude": "nonexistentCells"}
        data = await self._transport.request("GET", f"/sheets/{sheet_id}", params=params)
        return mappers.to_sheet(data)

    async def sheet_workspace_id(self, sheet_id: str) -> str | None:
        """Lee el workspace actual de la hoja, sin usar caché."""
        data = await self._transport.request(
            "GET", f"/sheets/{sheet_id}", params={"pageSize": 1, "page": 1}
        )
        return mappers.sheet_workspace_id(data)

    async def sheet_version(self, sheet_id: str) -> int:
        """Versión actual de una hoja, consultada sin caché."""
        data = await self._transport.request("GET", f"/sheets/{sheet_id}/version")
        return int(data["version"])

    async def list_sheet_shares(self, sheet_id: str) -> list[RawShare]:
        params = _asset(sheet_id) | {"sharingInclude": _SHARING_INCLUDE}
        return [
            mappers.to_share(item) for item in await self._transport.get_items(SHARES_PATH, params)
        ]

    async def get_sheet_share(self, sheet_id: str, share_id: str) -> RawShare:
        data = await self._transport.request(
            "GET", f"{SHARES_PATH}/{share_id}", params=_asset(sheet_id)
        )
        return mappers.to_share(data)

    async def list_users(self) -> list[RawUser]:
        items = await self._transport.get_all("/users", {"include": "lastLogin"})
        return [mappers.to_user(item) for item in items]

    async def list_groups(self) -> list[RawGroup]:
        return [mappers.to_group(item) for item in await self._transport.get_all("/groups")]

    async def list_contacts(self) -> list[RawContact]:
        return [mappers.to_contact(item) for item in await self._transport.get_all("/contacts")]

    async def list_columns(self, sheet_id: str) -> list[RawColumn]:
        items = await self._transport.get_all(f"/sheets/{sheet_id}/columns")
        return [mappers.to_column(item) for item in items]

    async def list_rows(
        self, sheet_id: str, column_ids: list[str], *, with_authors: bool = False
    ) -> list[RawRow]:
        """Todas las filas, sólo con las columnas pedidas; la primera es la etiqueta.

        Pedir pocas columnas mantiene liviana una hoja de miles de filas y 100+ columnas.
        """
        rows: list[RawRow] = []
        label = column_ids[0] if column_ids else None
        page = 1
        while True:
            params: dict[str, Any] = {
                "columnIds": ",".join(column_ids),
                "pageSize": _ROWS_PAGE,
                "page": page,
            }
            if with_authors:
                params["include"] = "writerInfo"
            data = await self._transport.request("GET", f"/sheets/{sheet_id}", params=params)
            batch = data.get("rows", [])
            rows.extend(mappers.to_row(item, label) for item in batch)
            # Smartsheet repite la última página si se pide una mayor: cortar por total.
            if len(batch) < _ROWS_PAGE or len(rows) >= int(data.get("totalRowCount") or 0):
                return rows
            page += 1

    async def list_automation_rules(self, sheet_id: str) -> list[RawAutomation]:
        items = await self._transport.get_all(f"/sheets/{sheet_id}/automationrules")
        return [mappers.to_automation(item) for item in items]

    async def get_row_filled_columns(self, sheet_id: str, row_id: str) -> list[str]:
        """Columnas con valor en una fila: las que tienen historial que mostrar."""
        data = await self._transport.request("GET", f"/sheets/{sheet_id}/rows/{row_id}")
        return [
            str(cell["columnId"])
            for cell in data.get("cells", [])
            if cell.get("value") is not None or cell.get("displayValue")
        ]

    async def get_row(self, sheet_id: str, row_id: str) -> RawRow:
        """Fila actual sin caché."""
        data = await self._transport.request("GET", f"/sheets/{sheet_id}/rows/{row_id}")
        return mappers.to_row(data)

    async def update_stable_id_once(
        self, sheet_id: str, row_id: str, value: str, expected: str = ""
    ) -> None:
        """Escribe una celda Stable ID con barreras; no es atómica frente a otros editores.

        Sólo escribe si la celda contiene `expected`: vacía por defecto; el ID copiado de otra
        madre cuando se renumera una copia (SPEC-ID01 ID-42).
        """
        from app.core.errors import AppError
        from app.services.ids import pilot
        from app.services.permissions import AccessLevel

        # Sólo las hojas configuradas del ID Manager y su columna Stable ID.
        allowed = {item[0]: item[3] for item in pilot.SHEETS}
        if (
            self._settings.app_read_only
            or not self._settings.ids_writes_enabled
            or not self._settings.ids_transition_approved
            or sheet_id not in allowed
        ):
            raise AppError("IDS_WRITE_BLOCKED", "Escrituras de IDs deshabilitadas.", 403)
        if await self.sheet_workspace_id(sheet_id) != "7965022790936452":
            raise AppError("IDS_WORKSPACE_BLOCKED", "Hoja fuera del workspace permitido.", 403)
        access = await self.get_sheet_access_level(sheet_id)
        if access.access_level not in (AccessLevel.ADMIN, AccessLevel.OWNER):
            raise AppError("IDS_ACCESS_BLOCKED", "Sin acceso de administración a la hoja.", 403)
        columns = await self.list_columns(sheet_id)
        matches = [c.id for c in columns if c.title == allowed[sheet_id]]
        if len(matches) != 1:
            raise AppError(
                "IDS_COLUMN_INVALID", "Columna Stable ID no encontrada o duplicada.", 409
            )
        row = await self.get_row(sheet_id, row_id)
        if (row.cells.get(matches[0]) or "").strip() != expected:
            code = "IDS_STABLE_CHANGED" if expected else "IDS_STABLE_EXISTS"
            raise AppError(code, "El Stable ID contiene otro valor.", 409)
        body = [{"id": int(row_id), "cells": [{"columnId": int(matches[0]), "value": value}]}]
        await self._transport.request("PUT", f"/sheets/{sheet_id}/rows", json=body, retry=False)

    async def upsert_catalog_rows(self, sheet_id: str, add: list[dict], update: list[dict]) -> None:
        """Agrega o actualiza filas de la hoja catálogo; nunca borra. Barreras en el llamador."""
        from app.core.errors import AppError

        if self._settings.app_read_only:
            raise AppError("CATALOG_WRITE_BLOCKED", "Escrituras del catálogo deshabilitadas.", 403)
        if add:
            await self._transport.request("POST", f"/sheets/{sheet_id}/rows", json=add, retry=False)
        if update:
            await self._transport.request(
                "PUT", f"/sheets/{sheet_id}/rows", json=update, retry=False
            )

    async def sort_catalog_rows(self, sheet_id: str, column_ids: list[str]) -> None:
        """Ordena la hoja catálogo (ascendente por esas columnas); no cambia valores."""
        from app.core.errors import AppError

        if self._settings.app_read_only:
            raise AppError("CATALOG_WRITE_BLOCKED", "Escrituras del catálogo deshabilitadas.", 403)
        criteria = [{"columnId": int(item), "direction": "ASCENDING"} for item in column_ids]
        await self._transport.request(
            "POST", f"/sheets/{sheet_id}/sort", json={"sortCriteria": criteria}, retry=False
        )

    async def get_cell_history(
        self, sheet_id: str, row_id: str, column_id: str
    ) -> list[RawCellChange]:
        path = f"/sheets/{sheet_id}/rows/{row_id}/columns/{column_id}/history"
        return [mappers.to_cell_change(item) for item in await self._transport.get_all(path)]

    async def list_row_comments(self, sheet_id: str) -> list[RawComment]:
        """Comentarios de las conversaciones de filas de la hoja (SPEC-B17 OB-14)."""
        items = await self._transport.get_all(
            f"/sheets/{sheet_id}/discussions", {"include": "comments"}
        )
        return [comment for item in items for comment in mappers.to_row_comments(item)]

    async def update_row_text(self, sheet_id: str, row_id: str, column_id: str, text: str) -> None:
        """Reescribe una celda de texto de una fila; barreras de hoja en el llamador."""
        self._require_writes()
        body = [{"id": int(row_id), "cells": [{"columnId": int(column_id), "value": text}]}]
        await self._transport.request("PUT", f"/sheets/{sheet_id}/rows", json=body, retry=False)

    async def add_row_comment(self, sheet_id: str, row_id: str, text: str) -> str | None:
        """Conversación nueva en una fila; devuelve el id del comentario creado."""
        self._require_writes()
        data = await self._transport.request(
            "POST",
            f"/sheets/{sheet_id}/rows/{row_id}/discussions",
            json={"comment": {"text": text}},
            retry=False,
        )
        comments = (data.get("result") or {}).get("comments") or [{}]
        created = comments[0].get("id")
        return None if created is None else str(created)

    async def move_row_after(self, sheet_id: str, row_id: str, sibling_id: str) -> None:
        """Mueve una fila al mismo nivel que `sibling_id`, debajo de ella y de sus hijas."""
        self._require_writes()
        body = [{"id": int(row_id), "siblingId": int(sibling_id)}]
        await self._transport.request("PUT", f"/sheets/{sheet_id}/rows", json=body, retry=False)

    def _require_writes(self) -> None:
        from app.core.errors import AppError

        if self._settings.app_read_only:
            raise AppError("WRITE_BLOCKED", "Escrituras deshabilitadas (solo lectura).", 403)

    # Escrituras (bloqueadas antes de llegar aquí en modo solo lectura)

    async def create_sheet_shares(
        self, sheet_id: str, shares: list[NewShare], message: ShareMessage | None
    ) -> None:
        params = _asset(sheet_id) | {"sendEmail": "true" if message else "false"}
        body = [_share_body(share, message) for share in shares]
        await self._transport.request("POST", SHARES_PATH, params=params, json=body)

    async def update_sheet_share(self, sheet_id: str, share_id: str, level: str) -> None:
        path = f"{SHARES_PATH}/{share_id}"
        await self._transport.request(
            "PATCH", path, params=_asset(sheet_id), json={"accessLevel": level}
        )

    async def delete_sheet_share(self, sheet_id: str, share_id: str) -> None:
        await self._transport.request(
            "DELETE", f"{SHARES_PATH}/{share_id}", params=_asset(sheet_id)
        )


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
