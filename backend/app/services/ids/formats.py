"""Formato y ámbito de IDs; funciones puras sin acceso a datos."""

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class EntityKind(StrEnum):
    PROJECT = "project"
    TASK = "task"
    RECORD = "record"
    REVISION = "revision"


# Proyecto con cliente (`KMV-CC-26-001`) o sólo con año (`KMV-26-0001`, ID-52).
_SCOPE = r"[A-Z0-9]+-(?:[A-Z0-9]+-)?[0-9]{2}"
_PROJECT = _SCOPE + r"-[0-9]{3,}"
_TASK = _PROJECT + r"-[0-9]{2,}"
_PATTERNS = {
    EntityKind.PROJECT: re.compile(rf"(?P<parent>{_SCOPE})-(?P<num>[0-9]{{3,}})"),
    EntityKind.TASK: re.compile(rf"(?P<parent>{_PROJECT})-(?P<num>[0-9]{{2,}})"),
    EntityKind.RECORD: re.compile(rf"(?P<parent>{_TASK})-R(?P<num>[0-9]+)"),
    EntityKind.REVISION: re.compile(rf"(?P<parent>{_TASK})-V(?P<num>[0-9]+)"),
}


def project_scope(
    company: str, customer: str, received: date | None, *, with_customer: bool = True
) -> str:
    """Ámbito usando exclusivamente el año de recepción del proyecto.

    Sin cliente en el ID (ID-52) el cliente sigue siendo obligatorio para numerar.
    """
    company, customer = company.strip(), customer.strip()
    if not company or not customer or not received or not 2000 <= received.year <= 2099:
        return ""
    year = f"{received.year % 100:02d}"
    return f"{company}-{customer}-{year}" if with_customer else f"{company}-{year}"


def customer_code(scope: str) -> str:
    """Código de cliente de un ámbito de proyecto (`KMV-CC-26` -> `CC`); vacío si no aplica."""
    parts = scope.split("-")
    return parts[1] if len(parts) == 3 else ""


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
    # Con un solo contador por año (sin cliente) el número lleva 4 dígitos (ID-52).
    width = 4 if parent.count("-") == 1 else 3
    suffix = {
        EntityKind.PROJECT: f"{number:0{width}d}",
        EntityKind.TASK: f"{number:02d}",
        EntityKind.RECORD: f"R{number}",
        EntityKind.REVISION: f"V{number}",
    }[kind]
    value = f"{parent}-{suffix}"
    match = _PATTERNS[kind].fullmatch(value)
    if match is None or match.group("parent") != parent:
        raise ValueError("Formato de identificador o ámbito inválido")
    return value


def formula_number(kind: EntityKind, parent: str, visible: str) -> int | None:
    """Número que propone la fórmula de Smartsheet si es canónico y del mismo padre."""
    try:
        parts = parse_id(kind, visible.strip())
    except ValueError:
        return None
    return parts.number if parts.parent == parent else None


def parse_id(kind: EntityKind, value: str) -> IdParts:
    """Acepta sólo IDs canónicos para impedir colisiones por ceros o formato."""
    match = _PATTERNS[kind].fullmatch(value)
    if match is None:
        raise ValueError("Formato de identificador inválido")
    parts = IdParts(kind, match.group("parent"), int(match.group("num")))
    if make_id(kind, parts.parent, parts.number) != value:
        raise ValueError("Identificador no canónico")
    return parts
