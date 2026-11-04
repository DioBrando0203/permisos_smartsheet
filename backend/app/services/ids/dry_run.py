"""Decisiones de simulación de IDs; no reserva, consulta ni escribe."""

from dataclasses import dataclass
from enum import StrEnum

from app.services.ids.formats import EntityKind, parse_id

PILOT_WORKSPACE = "7965022790936452"


class PlanAction(StrEnum):
    DENIED = "denied"
    PENDING_PARENT = "pending_parent"
    PENDING_DATA = "pending_data"
    PENDING_FORMULA = "pending_formula"
    CONFLICT = "conflict"
    ALREADY_STABLE = "already_stable"
    CONFIRM_RESERVATION = "confirm_reservation"
    REGISTER_EXISTING = "register_existing"
    NEEDS_RESERVATION = "needs_reservation"
    WOULD_WRITE = "would_write"


@dataclass(frozen=True)
class Candidate:
    sheet_id: str
    workspace_id: str | None
    kind: EntityKind
    parent: str
    parent_confirmed: bool
    visible_id: str
    stable_id: str
    reserved_id: str | None
    reserved_state: str | None = None


def plan(candidate: Candidate, allowed_sheets: frozenset[str]) -> PlanAction:
    """Aplica barreras de seguridad; el resultado no autoriza una escritura.

    Política 2026-11-04: la fórmula sólo propone el número. Un ID confirmado es permanente
    aunque cambien los datos; un Stable ID sin rastro se registra; sólo es conflicto un Stable
    ID inválido, de otro padre o distinto de la reserva de la fila.
    """
    if candidate.workspace_id != PILOT_WORKSPACE or candidate.sheet_id not in allowed_sheets:
        return PlanAction.DENIED
    visible = candidate.visible_id.strip()
    stable = candidate.stable_id.strip()
    if stable and (candidate.reserved_id, candidate.reserved_state) == (stable, "confirmado"):
        return PlanAction.ALREADY_STABLE
    if not candidate.parent_confirmed:
        return PlanAction.PENDING_PARENT
    if stable:
        try:
            if parse_id(candidate.kind, stable).parent != candidate.parent:
                return PlanAction.CONFLICT
        except ValueError:
            return PlanAction.CONFLICT
        if candidate.reserved_id is None:
            return PlanAction.REGISTER_EXISTING
        if candidate.reserved_id != stable:
            return PlanAction.CONFLICT
        return PlanAction.CONFIRM_RESERVATION
    if candidate.reserved_id is not None:
        return PlanAction.WOULD_WRITE
    return PlanAction.NEEDS_RESERVATION if visible else PlanAction.PENDING_FORMULA
