"""Planes puros de operaciones masivas (SPEC-B06): qué se haría, sin E/S.

Copiar sólo agrega o sube niveles; nunca baja ni quita (ADR-B13).
"""

from dataclasses import dataclass
from enum import StrEnum

from app.services.directory import person_key
from app.services.permissions import AccessLevel, ShareScope, ShareType, rank
from app.services.smartsheet import RawShare


class StepAction(StrEnum):
    CREATE = "CREATE"
    UPGRADE = "UPGRADE"
    KEEP = "KEEP"
    SKIP = "SKIP"
    REMOVE = "REMOVE"


@dataclass(frozen=True)
class PersonLevel:
    """Nivel efectivo de una persona en una hoja: el más alto entre propio y heredado."""

    key: str
    type: ShareType
    name: str | None
    email: str | None
    group_id: str | None
    level: AccessLevel
    item_share: RawShare | None  # permiso propio de la hoja, si existe


@dataclass(frozen=True)
class PlannedStep:
    action: StepAction
    person: PersonLevel
    new_level: AccessLevel | None
    current_level: AccessLevel | None
    share_id: str | None
    reason: str | None


def effective_levels(
    shares: list[RawShare], *, include_inherited: bool = True
) -> dict[str, PersonLevel]:
    result: dict[str, PersonLevel] = {}
    for share in shares:
        if share.scope is ShareScope.WORKSPACE and not include_inherited:
            continue
        item_id = share.group_id if share.type is ShareType.GROUP else share.user_id
        key = person_key(share.type, share.email, item_id)
        result[key] = _merge(result.get(key), key, share)
    return result


def plan_copy(
    source: list[RawShare],
    target: list[RawShare],
    *,
    upgrade_levels: bool,
    include_inherited: bool,
) -> list[PlannedStep]:
    """Qué pasaría en la hoja destino si se copian los accesos de la hoja origen."""
    wanted = effective_levels(source, include_inherited=include_inherited)
    current = effective_levels(target)
    return [
        _copy_step(person, current.get(key), upgrade_levels)
        for key, person in sorted(wanted.items())
    ]


def _copy_step(
    source: PersonLevel, target: PersonLevel | None, upgrade_levels: bool
) -> PlannedStep:
    # Copiar OWNER transferiría la propiedad; se copia como ADMIN (ADR-B04).
    level = AccessLevel.ADMIN if source.level is AccessLevel.OWNER else source.level
    if target is None:
        return PlannedStep(StepAction.CREATE, source, level, None, None, None)
    current = target.level
    if current is AccessLevel.OWNER:
        return PlannedStep(StepAction.SKIP, source, level, current, None, "OWNER")
    if rank(current) >= rank(level):
        return PlannedStep(StepAction.KEEP, source, level, current, None, "SAME_OR_HIGHER")
    if target.item_share is None:
        return PlannedStep(StepAction.SKIP, source, level, current, None, "INHERITED")
    if not upgrade_levels:
        return PlannedStep(StepAction.KEEP, source, level, current, None, "LOWER_LEVEL_KEPT")
    return PlannedStep(StepAction.UPGRADE, source, level, current, target.item_share.id, None)


def _merge(previous: PersonLevel | None, key: str, share: RawShare) -> PersonLevel:
    item = share if share.scope is ShareScope.ITEM else None
    if previous is None:
        return PersonLevel(
            key, share.type, share.name, share.email, share.group_id, share.access_level, item
        )
    level = max(previous.level, share.access_level, key=rank)
    return PersonLevel(
        key,
        previous.type,
        previous.name or share.name,
        previous.email,
        previous.group_id,
        level,
        previous.item_share or item,
    )
