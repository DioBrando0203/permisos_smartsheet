"""Permisos de una hoja: listar, dar, cambiar y quitar acceso (SPEC-B02).

Toda escritura comprueba el modo solo lectura, lee datos frescos de Smartsheet, aplica
`permissions.rules` y responde con el estado releído (SM-06, SM-08).
"""

from collections.abc import Awaitable
from typing import TypeVar

from app.core.errors import AppError
from app.models.shares import (
    Share,
    ShareCreate,
    ShareCreateResult,
    ShareList,
    SkippedRecipient,
)
from app.services.cache import TtlCache
from app.services.permissions import (
    AccessLevel,
    LockedReason,
    ShareScope,
    find_duplicates,
    is_assignable,
    lock_reason,
    share_sort_key,
)
from app.services.sheets import SheetService, sheet_not_found
from app.services.smartsheet import NewShare, RawShare, ShareMessage, SmartsheetClient

PEOPLE_KEY = "people"
T = TypeVar("T")

_LOCK_ERRORS = {
    LockedReason.OWNER: (
        "OWNER_LOCKED",
        "El permiso del propietario no se cambia desde el panel.",
        409,
    ),
    LockedReason.INHERITED: (
        "SHARE_INHERITED",
        "Este acceso se hereda del workspace; cámbielo en el workspace.",
        409,
    ),
    LockedReason.NO_PERMISSION: (
        "CANNOT_MANAGE_SHARES",
        "La cuenta del token no es Administrador ni Propietario de esta hoja.",
        403,
    ),
}


def shares_key(sheet_id: str) -> str:
    return f"shares:{sheet_id}"


class ShareService:
    def __init__(
        self, client: SmartsheetClient, cache: TtlCache, sheets: SheetService, *, read_only: bool
    ) -> None:
        self._client = client
        self._cache = cache
        self._sheets = sheets
        self._read_only = read_only

    async def raw_shares(self, sheet_id: str, *, refresh: bool = False) -> list[RawShare]:
        async def load() -> list[RawShare]:
            return await _as_sheet_error(self._client.list_sheet_shares(sheet_id))

        return await self._cache.get_or_load(shares_key(sheet_id), load, refresh=refresh)

    async def list(self, sheet_id: str, *, refresh: bool = False) -> ShareList:
        sheet = await self._sheets.find(sheet_id)
        raw = await self.raw_shares(sheet_id, refresh=refresh)
        token_level = sheet.access_level if sheet else None
        return ShareList(
            sheet_id=sheet_id,
            shares=sort_shares([to_share(share, token_level) for share in raw]),
            loaded_at=self._cache.loaded_at(shares_key(sheet_id)),
        )

    async def create(self, sheet_id: str, request: ShareCreate) -> ShareCreateResult:
        self._ensure_writable()
        _ensure_assignable(request.access_level)
        _ensure_unique(request)
        token_level = await self._fresh_token_level(sheet_id)
        _raise_if_locked(lock_reason(request.access_level, ShareScope.ITEM, token_level))
        current = await self.raw_shares(sheet_id, refresh=True)
        pending, skipped = split_new_recipients(request, current)
        if not pending:
            return ShareCreateResult(created=[], skipped=skipped)
        message = ShareMessage(request.subject, request.message) if request.send_email else None
        await _as_sheet_error(self._client.create_sheet_shares(sheet_id, pending, message))
        self._invalidate(sheet_id)
        wanted = {_new_share_key(share) for share in pending}
        fresh = await self.raw_shares(sheet_id, refresh=True)
        created = [
            to_share(share, token_level)
            for share in fresh
            if share.scope is ShareScope.ITEM and _share_key(share) in wanted
        ]
        return ShareCreateResult(created=sort_shares(created), skipped=skipped)

    async def update(self, sheet_id: str, share_id: str, level: AccessLevel) -> Share:
        self._ensure_writable()
        _ensure_assignable(level)
        share, token_level = await self._editable_share(sheet_id, share_id)
        if share.access_level is level:
            return to_share(share, token_level)
        await _as_share_error(self._client.update_sheet_share(sheet_id, share_id, str(level)))
        self._invalidate(sheet_id)
        updated = await _as_share_error(self._client.get_sheet_share(sheet_id, share_id))
        return to_share(updated, token_level)

    async def delete(self, sheet_id: str, share_id: str) -> None:
        self._ensure_writable()
        await self._editable_share(sheet_id, share_id)
        await _as_share_error(self._client.delete_sheet_share(sheet_id, share_id))
        self._invalidate(sheet_id)

    async def _editable_share(self, sheet_id: str, share_id: str) -> tuple[RawShare, AccessLevel]:
        token_level = await self._fresh_token_level(sheet_id)
        share = await _as_share_error(self._client.get_sheet_share(sheet_id, share_id))
        _raise_if_locked(lock_reason(share.access_level, share.scope, token_level))
        return share, token_level

    async def _fresh_token_level(self, sheet_id: str) -> AccessLevel:
        sheet = await _as_sheet_error(self._client.get_sheet_access_level(sheet_id))
        return sheet.access_level

    def _ensure_writable(self) -> None:
        if self._read_only:
            raise AppError(
                "READ_ONLY_MODE",
                "El panel está en modo solo lectura (APP_READ_ONLY=true). No se cambió nada.",
                403,
            )

    def _invalidate(self, sheet_id: str) -> None:
        self._cache.invalidate(shares_key(sheet_id))
        self._cache.invalidate(PEOPLE_KEY)


def to_share(share: RawShare, token_level: AccessLevel | None) -> Share:
    reason = lock_reason(share.access_level, share.scope, token_level)
    return Share(
        id=share.id,
        type=share.type,
        user_id=share.user_id,
        group_id=share.group_id,
        email=share.email,
        name=share.name,
        access_level=share.access_level,
        scope=share.scope,
        editable=reason is None,
        locked_reason=reason,
    )


def sort_shares(shares: list[Share]) -> list[Share]:
    return sorted(
        shares,
        key=lambda share: share_sort_key(
            share.access_level, share.type, share.name or share.email or ""
        ),
    )


def split_new_recipients(
    request: ShareCreate, current: list[RawShare]
) -> tuple[list[NewShare], list[SkippedRecipient]]:
    """Separa a quien ya tiene acceso propio (se omite, no se duplica) de quien falta."""
    existing = {_share_key(share): share for share in current if share.scope is ShareScope.ITEM}
    pending: list[NewShare] = []
    skipped: list[SkippedRecipient] = []
    for recipient in request.recipients:
        share = existing.get(recipient.key)
        if share is None:
            pending.append(NewShare(recipient.email, recipient.group_id, request.access_level))
            continue
        skipped.append(
            SkippedRecipient(
                recipient=recipient, reason="ALREADY_SHARED", current_level=share.access_level
            )
        )
    return pending, skipped


def _share_key(share: RawShare) -> str:
    return share.email or f"group-{share.group_id}"


def _new_share_key(share: NewShare) -> str:
    return share.email or f"group-{share.group_id}"


def _ensure_unique(request: ShareCreate) -> None:
    duplicates = find_duplicates([recipient.key for recipient in request.recipients])
    if duplicates:
        raise AppError(
            "DUPLICATE_RECIPIENTS", f"Destinatarios repetidos: {', '.join(duplicates)}.", 422
        )


def _ensure_assignable(level: AccessLevel) -> None:
    if not is_assignable(level):
        raise AppError(
            "OWNER_NOT_ASSIGNABLE",
            "El nivel Propietario transfiere la hoja; hágalo desde Smartsheet.",
            422,
        )


def _raise_if_locked(reason: LockedReason | None) -> None:
    if reason is not None:
        code, message, status = _LOCK_ERRORS[reason]
        raise AppError(code, message, status)


async def _as_sheet_error(call: Awaitable[T]) -> T:
    try:
        return await call
    except AppError as error:
        if error.code == "NOT_FOUND":
            raise sheet_not_found() from None
        raise


async def _as_share_error(call: Awaitable[T]) -> T:
    try:
        return await call
    except AppError as error:
        if error.code == "NOT_FOUND":
            raise AppError("SHARE_NOT_FOUND", "Ese acceso ya no existe en la hoja.", 404) from None
        raise
