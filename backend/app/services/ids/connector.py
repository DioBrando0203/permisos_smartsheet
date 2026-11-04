"""Coordinador de reservas y escritura comprobada; el adaptador real vive en `gateway.py`."""

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

import psycopg

from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind, parse_id
from app.services.ids.pilot import SHEETS
from app.services.ids.store import IdStore, Reservation


class Outcome(StrEnum):
    READ_ONLY = "read_only"
    DENIED = "denied"
    PENDING = "pending"
    CONFLICT = "conflict"
    EXISTING = "existing"
    CONFIRMED = "confirmed"


class WriteUncertain(Exception):
    """La escritura pudo aplicarse, pero no se recibió una respuesta confiable."""


@dataclass(frozen=True)
class Target:
    sheet_id: int
    row_id: int
    kind: EntityKind
    parent: str


@dataclass(frozen=True)
class Snapshot:
    workspace_id: str | None
    parent: str
    parent_confirmed: bool
    visible: str
    stable: str


class ConditionalGateway(Protocol):
    """Comprueba workspace, padre, ID visible y Stable ID antes de escribir."""

    async def read(self, target: Target) -> Snapshot: ...

    async def write_if_unchanged(self, target: Target, previous: Snapshot, value: str) -> bool:
        """True si se escribió; Smartsheet no garantiza atomicidad frente a otros editores."""
        ...


class IdConnector:
    """Procesa una fila: reserva, relee, escribe sólo celdas vacías y confirma tras releer."""

    def __init__(self, store: IdStore, gateway: ConditionalGateway, *, read_only: bool) -> None:
        self._store = store
        self._gateway = gateway
        self._read_only = read_only

    async def process(self, target: Target) -> Outcome:
        if self._read_only:
            return Outcome.READ_ONLY
        allowed = {(int(item[0]), item[1]) for item in SHEETS}
        if (target.sheet_id, target.kind) not in allowed:
            return Outcome.DENIED
        lock = await asyncio.to_thread(self._store.lock_sheet, target.sheet_id)
        if lock is None:
            return Outcome.PENDING
        try:
            return await self._process_locked(target, lock)
        finally:
            await asyncio.to_thread(lock.close)

    async def _process_locked(self, target: Target, lock: psycopg.Connection) -> Outcome:
        current = await self._gateway.read(target)
        if not _valid(target, current):
            return Outcome.DENIED
        reservation = await asyncio.to_thread(self._store.lookup, target.sheet_id, target.row_id)
        if reservation:
            try:
                if parse_id(target.kind, reservation.value).parent != target.parent:
                    return Outcome.CONFLICT
            except ValueError:
                return Outcome.CONFLICT
        if current.stable:
            return await self._reconcile(target, current, reservation)
        if reservation and reservation.state == "confirmado":
            return Outcome.CONFLICT
        if not current.parent_confirmed:
            return Outcome.PENDING
        if reservation is None:
            reservation = await asyncio.to_thread(
                self._store.reserve, target.sheet_id, target.row_id, target.kind, target.parent
            )
        current = await self._gateway.read(target)
        if not _valid(target, current) or not current.parent_confirmed:
            return Outcome.DENIED
        if current.stable:
            return await self._reconcile(target, current, reservation)
        if current.visible and current.visible != reservation.value:
            return Outcome.CONFLICT
        await asyncio.to_thread(lock.execute, "SELECT 1")
        try:
            if not await self._gateway.write_if_unchanged(target, current, reservation.value):
                return Outcome.CONFLICT
        except WriteUncertain:
            pass
        return await self._reconcile(target, await self._gateway.read(target), reservation)

    async def _reconcile(
        self, target: Target, current: Snapshot, reservation: Reservation | None
    ) -> Outcome:
        if not _valid(target, current):
            return Outcome.DENIED
        if not current.parent_confirmed:
            return Outcome.PENDING
        if not current.stable:
            return Outcome.PENDING
        if reservation is None:
            return Outcome.EXISTING
        if current.stable != reservation.value:
            return Outcome.CONFLICT
        await asyncio.to_thread(
            self._store.confirm, target.sheet_id, target.row_id, reservation.value
        )
        return Outcome.CONFIRMED


def _valid(target: Target, snapshot: Snapshot) -> bool:
    return snapshot.workspace_id == PILOT_WORKSPACE and snapshot.parent == target.parent
