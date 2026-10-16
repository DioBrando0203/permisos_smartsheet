"""Niveles de acceso de Smartsheet, su orden y etiquetas en español (tabla única, PY-13)."""

from enum import StrEnum


class AccessLevel(StrEnum):
    VIEWER = "VIEWER"
    COMMENTER = "COMMENTER"
    EDITOR = "EDITOR"
    EDITOR_SHARE = "EDITOR_SHARE"
    ADMIN = "ADMIN"
    OWNER = "OWNER"


class ShareType(StrEnum):
    USER = "USER"
    GROUP = "GROUP"


class ShareScope(StrEnum):
    ITEM = "ITEM"
    WORKSPACE = "WORKSPACE"


class LockedReason(StrEnum):
    OWNER = "OWNER"
    INHERITED = "INHERITED"
    NO_PERMISSION = "NO_PERMISSION"


_RANK = {level: position for position, level in enumerate(AccessLevel)}

LABELS = {
    AccessLevel.VIEWER: "Visor",
    AccessLevel.COMMENTER: "Comentarista",
    AccessLevel.EDITOR: "Editor",
    AccessLevel.EDITOR_SHARE: "Editor que comparte",
    AccessLevel.ADMIN: "Administrador",
    AccessLevel.OWNER: "Propietario",
}

# Niveles con los que el token puede administrar los permisos de una hoja.
MANAGER_LEVELS = frozenset({AccessLevel.ADMIN, AccessLevel.OWNER})


def rank(level: AccessLevel) -> int:
    return _RANK[level]


def highest(levels: list[AccessLevel]) -> AccessLevel | None:
    return max(levels, key=rank, default=None)


def can_manage_shares(token_level: AccessLevel | None) -> bool:
    return token_level in MANAGER_LEVELS
