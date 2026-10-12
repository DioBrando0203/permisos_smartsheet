"""Reglas puras sobre qué permisos se pueden crear, cambiar o quitar (ADR-B04, ADR-B05).

No hace E/S ni lanza errores HTTP: devuelve motivos que el servicio traduce.
"""

from app.services.permissions.levels import (
    AccessLevel,
    LockedReason,
    ShareScope,
    ShareType,
    can_manage_shares,
    rank,
)


def lock_reason(
    share_level: AccessLevel, scope: ShareScope, token_level: AccessLevel | None
) -> LockedReason | None:
    """Motivo por el que un permiso no se puede cambiar ni quitar desde la hoja, o `None`."""
    if share_level is AccessLevel.OWNER:
        return LockedReason.OWNER
    if scope is ShareScope.WORKSPACE:
        return LockedReason.INHERITED
    if token_level is None or not can_manage_shares(token_level):
        return LockedReason.NO_PERMISSION
    return None


def is_assignable(level: AccessLevel) -> bool:
    """`OWNER` transfiere la propiedad de la hoja: nunca se asigna desde el panel."""
    return level is not AccessLevel.OWNER


def find_duplicates(keys: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for key in keys:
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def share_sort_key(level: AccessLevel, share_type: ShareType, label: str) -> tuple[int, int, str]:
    """Nivel descendente, grupos antes que usuarios y luego nombre (SPEC-B02)."""
    return (-rank(level), 0 if share_type is ShareType.GROUP else 1, label.casefold())
