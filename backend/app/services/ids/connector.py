"""Coordinador de reservas y escritura comprobada; el adaptador real vive en `gateway.py`."""

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

import psycopg

from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind, formula_number, parse_id
from app.services.ids.store import IdStore, Reservation


class Outcome(StrEnum):
    READ_ONLY = "read_only"
    DENIED = "denied"
    PENDING = "pending"
    CONFLICT = "conflict"
    EXISTING = "existing"
    CONFIRMED = "confirmed"
    REGISTERED = "registered"
    INHERITED = "inherited"  # fila hija con el ID de su madre


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


@dataclass(frozen=True)
class ChildSnapshot:
    """Fila hija: su Stable ID y el de la fila de primer nivel de la que hereda."""

    workspace_id: str | None
    root_row: int | None
    root_stable: str
    stable: str


class ConditionalGateway(Protocol):
    """Comprueba workspace, padre, ID visible y Stable ID antes de escribir."""

    async def read(self, target: Target) -> Snapshot: ...

    async def write_if_unchanged(self, target: Target, previous: Snapshot, value: str) -> bool:
        """True si se escribió; Smartsheet no garantiza atomicidad frente a otros editores."""
        ...

    async def read_child(self, target: Target) -> ChildSnapshot: ...

    async def write_child(self, target: Target, value: str) -> bool: ...

    async def replace_copy(self, target: Target, copied: str, value: str) -> bool: ...

    async def read_stable(self, target: Target, row_id: int) -> str: ...


class IdConnector:
    """Procesa una fila: reserva, relee, escribe sólo celdas vacías y confirma tras releer."""

    def __init__(self, store: IdStore, gateway: ConditionalGateway, *, read_only: bool) -> None:
        self._store = store
        self._gateway = gateway
        self._read_only = read_only

    async def process(self, target: Target) -> Outcome:
        if self._read_only:
            return Outcome.READ_ONLY
        allowed = {(int(item[0]), item[1]) for item in pilot.SHEETS}
        if (target.sheet_id, target.kind) not in allowed:
            return Outcome.DENIED
        lock = await asyncio.to_thread(self._store.lock_sheet, target.sheet_id)
        if lock is None:
            return Outcome.PENDING
        try:
            return await self._process_locked(target, lock)
        finally:
            await asyncio.to_thread(lock.close)

    async def inherit(self, target: Target, mother_row: int) -> Outcome:
        """Fila hija: escribe el ID ya confirmado de su madre; no reserva ni gasta número."""
        if self._read_only:
            return Outcome.READ_ONLY
        if pilot.sheet_spec(target.sheet_id) is None:
            return Outcome.DENIED
        lock = await asyncio.to_thread(self._store.lock_sheet, target.sheet_id)
        if lock is None:
            return Outcome.PENDING
        try:
            current = await self._gateway.read_child(target)
            blocked = await self._check_child(target, current, mother_row)
            if blocked is not None:
                return blocked
            await asyncio.to_thread(lock.execute, "SELECT 1")
            try:
                await self._gateway.write_child(target, current.root_stable)
            except WriteUncertain:
                pass
            after = await self._gateway.read_child(target)
            if after.stable == current.root_stable:
                return Outcome.INHERITED
            return Outcome.CONFLICT if after.stable else Outcome.PENDING
        finally:
            await asyncio.to_thread(lock.close)

    async def renumber_copy(self, target: Target, original_row: int) -> Outcome:
        """Copia de una madre: la original conserva su ID y la copia recibe el siguiente."""
        if self._read_only:
            return Outcome.READ_ONLY
        if (target.sheet_id, target.kind) not in {(int(i[0]), i[1]) for i in pilot.SHEETS}:
            return Outcome.DENIED
        lock = await asyncio.to_thread(self._store.lock_sheet, target.sheet_id)
        if lock is None:
            return Outcome.PENDING
        try:
            current = await self._gateway.read(target)
            if not _valid(target, current) or not current.parent_confirmed:
                return Outcome.DENIED
            copied = current.stable
            owner = await asyncio.to_thread(self._store.confirmed_parent, target.sheet_id, copied)
            if not copied or owner != original_row or owner == target.row_id:
                return Outcome.CONFLICT
            if await self._gateway.read_stable(target, original_row) != copied:
                return Outcome.CONFLICT  # la original ya no existe o cambió: revisión humana
            reservation = await asyncio.to_thread(
                self._store.lookup, target.sheet_id, target.row_id
            )
            if reservation is None:
                reservation = await asyncio.to_thread(
                    self._store.reserve, target.sheet_id, target.row_id, target.kind, target.parent
                )
            elif reservation.state != "reservado":
                return Outcome.CONFLICT
            await asyncio.to_thread(lock.execute, "SELECT 1")
            try:
                await self._gateway.replace_copy(target, copied, reservation.value)
            except WriteUncertain:
                pass
            after = await self._gateway.read(target)
            if after.stable == copied:
                return Outcome.PENDING  # no se aplicó: se reintenta con la misma reserva
            return await self._reconcile(target, after, reservation)
        finally:
            await asyncio.to_thread(lock.close)

    async def _check_child(
        self, target: Target, current: ChildSnapshot, mother_row: int
    ) -> Outcome | None:
        """None si se puede escribir; si no, el resultado sin tocar la hoja."""
        if current.workspace_id != PILOT_WORKSPACE:
            return Outcome.DENIED
        if current.root_row != mother_row or not current.root_stable:
            return Outcome.PENDING
        owner = await asyncio.to_thread(
            self._store.confirmed_parent, target.sheet_id, current.root_stable
        )
        if owner != mother_row:
            return Outcome.PENDING
        if current.stable == current.root_stable:
            return Outcome.INHERITED
        return Outcome.CONFLICT if current.stable else None

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
            if reservation is None:
                return await self._register(target, current)
            return await self._reconcile(target, current, reservation)
        if not current.parent_confirmed:
            return Outcome.PENDING
        if reservation is None:
            # La fórmula propone el número; se adopta si es nuevo, si no, el siguiente libre.
            preferred = formula_number(target.kind, target.parent, current.visible)
            reservation = await asyncio.to_thread(
                self._store.reserve,
                target.sheet_id,
                target.row_id,
                target.kind,
                target.parent,
                preferred,
            )
        current = await self._gateway.read(target)
        if not _valid(target, current) or not current.parent_confirmed:
            return Outcome.DENIED
        if current.stable:
            return await self._reconcile(target, current, reservation)
        # Una reserva confirmada con la celda vaciada se restaura: el ID es permanente.
        await asyncio.to_thread(lock.execute, "SELECT 1")
        try:
            if not await self._gateway.write_if_unchanged(target, current, reservation.value):
                return Outcome.CONFLICT
        except WriteUncertain:
            pass
        return await self._reconcile(target, await self._gateway.read(target), reservation)

    async def _register(self, target: Target, current: Snapshot) -> Outcome:
        """Stable ID presente sin rastro en PostgreSQL: se registra tal cual, nunca se cambia."""
        if not current.parent_confirmed:
            return Outcome.PENDING
        try:
            if parse_id(target.kind, current.stable).parent != target.parent:
                return Outcome.CONFLICT
            await asyncio.to_thread(
                self._store.register_existing,
                target.sheet_id,
                target.row_id,
                target.kind,
                current.stable,
            )
        except ValueError:
            return Outcome.CONFLICT
        return Outcome.REGISTERED

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
