"""Formato y ámbito de IDs; funciones puras sin acceso a datos."""

import re
from dataclasses import dataclass
from enum import StrEnum


class EntityKind(StrEnum):
    PROJECT = "project"
    TASK = "task"
    RECORD = "record"
    REVISION = "revision"


_PROJECT = r"[A-Z0-9]+-[A-Z0-9]+-[0-9]{2}-[0-9]{3,}"
_TASK = _PROJECT + r"-[0-9]{2,}"
_PATTERNS = {
    EntityKind.PROJECT: re.compile(r"(?P<parent>[A-Z0-9]+-[A-Z0-9]+-[0-9]{2})-(?P<num>[0-9]{3,})"),
    EntityKind.TASK: re.compile(rf"(?P<parent>{_PROJECT})-(?P<num>[0-9]{{2,}})"),
    EntityKind.RECORD: re.compile(rf"(?P<parent>{_TASK})-R(?P<num>[0-9]+)"),
    EntityKind.REVISION: re.compile(rf"(?P<parent>{_TASK})-V(?P<num>[0-9]+)"),
}


@dataclass(frozen=True)
class IdParts:
    kind: EntityKind
    parent: str
    number: int

    @property
    def scope(self) -> str:
        return f"{self.kind.value}:{self.parent}"


def make_id(kind: EntityKind, parent: str, number: int) -> str:
    """Construye y valida el ID completo, sin normalizar silenciosamente sus componentes."""
    if number <= 0:
        raise ValueError("El consecutivo debe ser positivo")
    suffix = {
        EntityKind.PROJECT: f"{number:03d}",
        EntityKind.TASK: f"{number:02d}",
        EntityKind.RECORD: f"R{number}",
        EntityKind.REVISION: f"V{number}",
    }[kind]
    value = f"{parent}-{suffix}"
    match = _PATTERNS[kind].fullmatch(value)
    if match is None or match.group("parent") != parent:
        raise ValueError("Formato de identificador o ámbito inválido")
    return value


def parse_id(kind: EntityKind, value: str) -> IdParts:
    """Acepta sólo IDs canónicos para impedir colisiones por ceros o formato."""
    match = _PATTERNS[kind].fullmatch(value)
    if match is None:
        raise ValueError("Formato de identificador inválido")
    parts = IdParts(kind, match.group("parent"), int(match.group("num")))
    if make_id(kind, parts.parent, parts.number) != value:
        raise ValueError("Identificador no canónico")
    return parts
