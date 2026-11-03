"""Decisiones de simulación de IDs; no reserva, consulta ni escribe."""

from dataclasses import dataclass
from enum import StrEnum

from app.services.ids.formats import EntityKind, parse_id

PILOT_WORKSPACE = "7965022790936452"


class PlanAction(StrEnum):
    DENIED = "denied"
    PENDING_PARENT = "pending_parent"
    PENDING_FORMULA = "pending_formula"
    CONFLICT = "conflict"
    ALREADY_STABLE = "already_stable"
    CONFIRM_RESERVATION = "confirm_reservation"
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
    """Aplica barreras de seguridad; el resultado no autoriza una escritura."""
    if candidate.workspace_id != PILOT_WORKSPACE or candidate.sheet_id not in allowed_sheets:
        return PlanAction.DENIED
    if not candidate.parent_confirmed:
        return PlanAction.PENDING_PARENT
    visible = candidate.visible_id.strip()
    stable = candidate.stable_id.strip()
    if not visible and not stable:
        return PlanAction.PENDING_FORMULA
    try:
        parts = parse_id(candidate.kind, visible)
    except ValueError:
        return PlanAction.CONFLICT
    if parts.parent != candidate.parent:
        return PlanAction.CONFLICT
    if stable:
        if stable != visible or (candidate.reserved_id and candidate.reserved_id != stable):
            return PlanAction.CONFLICT
        if candidate.reserved_id and candidate.reserved_state == "reservado":
            return PlanAction.CONFIRM_RESERVATION
        return PlanAction.ALREADY_STABLE
    if candidate.reserved_id is None:
        return PlanAction.NEEDS_RESERVATION
    if candidate.reserved_id != visible:
        return PlanAction.CONFLICT
    return PlanAction.WOULD_WRITE
