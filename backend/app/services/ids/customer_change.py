"""Cambio de cliente (SPEC-ID01 ID-44 a ID-46): ID nuevo para la madre y familia coherente.

Mismo patrón que el resto del conector: bloqueo por hoja, registro en PostgreSQL antes de tocar
la hoja y relectura después de escribir. El rastro queda en la auditoría de PostgreSQL y en el
log, nunca en la hoja (nada técnico a la vista). Las referencias van al final y no deciden el
resultado: si fallan, sólo queda el aviso en el log.
"""

import asyncio
import logging

from app.core.errors import AppError
from app.services.ids.connector import ConditionalGateway, Outcome, Target, WriteUncertain
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import customer_code, parse_id
from app.services.ids.store import IdStore, Reservation

logger = logging.getLogger("app.ids")
REASON = "customer"


async def run(
    action: str, store: IdStore, gateway: ConditionalGateway, target: Target, mother_row: int
) -> Outcome:
    lock = await asyncio.to_thread(store.lock_sheet, target.sheet_id)
    if lock is None:
        return Outcome.PENDING
    try:
        if action == "rescope":
            return await _rescope(store, gateway, target, lock)
        if action == "detach_child":
            return await _detach(gateway, target, mother_row, lock)
        if action == "child_follow":
            return await _follow(store, gateway, target, mother_row, lock)
        return Outcome.DENIED
    finally:
        await asyncio.to_thread(lock.close)


async def _rescope(store: IdStore, gateway: ConditionalGateway, target: Target, lock) -> Outcome:
    """Madre cuyo cliente cambió: retira su ID y escribe el siguiente libre del cliente actual."""
    current = await gateway.read(target)
    if current.workspace_id != PILOT_WORKSPACE or current.parent != target.parent:
        return Outcome.DENIED
    old = current.stable
    if not old or _customer(target, old) in ("", customer_code(target.parent)):
        return Outcome.PENDING
    reservation = await _fresh_reservation(store, target, old)
    if reservation is None:
        return Outcome.CONFLICT
    await asyncio.to_thread(lock.execute, "SELECT 1")
    try:
        await gateway.replace_copy(target, old, reservation.value)
    except WriteUncertain:
        pass
    after = await gateway.read(target)
    if after.stable == old:
        return Outcome.PENDING  # no se aplicó: se reintenta con la misma reserva
    if after.stable != reservation.value:
        return Outcome.CONFLICT
    await asyncio.to_thread(store.confirm, target.sheet_id, target.row_id, reservation.value)
    await _relink(gateway, target, old, reservation.value)
    return Outcome.RESCOPED


async def _detach(gateway: ConditionalGateway, target: Target, mother_row: int, lock) -> Outcome:
    """Hija con otro cliente que su madre: pasa a primer nivel sin el ID heredado (ID-45)."""
    child = await gateway.read_child(target)
    if child.workspace_id != PILOT_WORKSPACE:
        return Outcome.DENIED
    if child.root_row != mother_row:
        return Outcome.PENDING
    mine, mother = await gateway.customer_codes(target, mother_row)
    if not mine or not mother or mine == mother:
        return Outcome.PENDING
    await asyncio.to_thread(lock.execute, "SELECT 1")
    await gateway.move_out(target, mother_row)
    if child.stable:
        # El ID heredado era de la madre: se borra para que reciba uno propio, limpio.
        try:
            await gateway.replace_copy(target, child.stable, "")
        except WriteUncertain:
            pass
    logger.info("ids hija %s fuera de la jerarquía en hoja %s", target.row_id, target.sheet_id)
    return Outcome.DETACHED


async def _follow(
    store: IdStore, gateway: ConditionalGateway, target: Target, mother_row: int, lock
) -> Outcome:
    """Hija que conserva el cliente y el ID anteriores de su madre: toma los actuales (ID-46)."""
    child = await gateway.read_child(target)
    if child.workspace_id != PILOT_WORKSPACE:
        return Outcome.DENIED
    if child.root_row != mother_row or not child.root_stable:
        return Outcome.PENDING
    owner = await asyncio.to_thread(store.confirmed_parent, target.sheet_id, child.root_stable)
    if owner != mother_row:
        return Outcome.PENDING
    mine, mother = await gateway.customer_codes(target, mother_row)
    await asyncio.to_thread(lock.execute, "SELECT 1")
    if mine != mother:
        if not child.stable or _customer(target, child.stable) != mine:
            return Outcome.PENDING  # ya no es el caso previsto: se reevalúa en el ciclo siguiente
        await gateway.copy_customer(target, mother_row)
    if child.stable != child.root_stable:
        try:
            await gateway.replace_copy(target, child.stable, child.root_stable)
        except WriteUncertain:
            pass
    after = await gateway.read_child(target)
    return Outcome.FOLLOWED if after.stable == child.root_stable else Outcome.PENDING


async def _fresh_reservation(store: IdStore, target: Target, old: str) -> Reservation | None:
    """Reserva del cliente actual; retira el ID anterior y cualquier reserva de otro cliente."""
    reservation = await asyncio.to_thread(store.lookup, target.sheet_id, target.row_id)
    if reservation is not None and (
        reservation.value == old
        or (reservation.state == "reservado" and _scope(target, reservation.value) != target.parent)
    ):
        await asyncio.to_thread(
            store.retire, target.sheet_id, target.row_id, reservation.value, REASON
        )
        reservation = None
    if reservation is None:
        reservation = await asyncio.to_thread(
            store.reserve, target.sheet_id, target.row_id, target.kind, target.parent
        )
    if reservation.state != "reservado" or _scope(target, reservation.value) != target.parent:
        return None
    return reservation


def _scope(target: Target, value: str) -> str:
    try:
        return parse_id(target.kind, value).parent
    except ValueError:
        return ""


def _customer(target: Target, value: str) -> str:
    return customer_code(_scope(target, value))


async def _relink(gateway: ConditionalGateway, target: Target, old: str, new: str) -> None:
    try:
        changed = await gateway.relink(target, old, new)
    except (AppError, ValueError):
        logger.warning("ids Linked Tracking sin actualizar en hoja %s", target.sheet_id)
        return
    if changed:
        logger.info("ids Linked Tracking actualizado en hoja %s: %s", target.sheet_id, changed)
