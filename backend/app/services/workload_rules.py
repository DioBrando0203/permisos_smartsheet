"""Reglas puras de la carga de diseñadores (SPEC-B12): estado, fase, asignaciones y personas."""

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

from app.models.people import Person
from app.services.permissions import ShareType
from app.services.search import normalize
from app.services.smartsheet import RawRow

RowState = Literal["open", "on_hold", "closed"]
_PHASE = re.compile(r"^\s*(\d+)\s*\.")


def is_placeholder(value: str | None) -> bool:
    """Vacío o un separador de lista desplegable (`-----`)."""
    text = (value or "").strip()
    return not text or set(text) <= {"-", " "}


def row_state(status: str | None, closed: set[str]) -> RowState:
    if is_placeholder(status):
        return "open"
    text = (status or "").strip().casefold()
    if text in closed:
        return "closed"
    return "on_hold" if "hold" in text else "open"


def phase_of(status: str | None) -> str:
    """El número antes del primer punto (`2. Design Process` es `2`); si no hay, `other`."""
    match = _PHASE.match(status or "")
    return match.group(1) if match else "other"


def designers_in_row(row: RawRow, column_ids: list[str], headers: set[str]) -> list[str]:
    """Nombres distintos de la fila; ignora vacíos, separadores y títulos de columna copiados."""
    seen: dict[str, str] = {}
    for column_id in column_ids:
        value = (row.cells.get(column_id) or "").strip()
        if is_placeholder(value) or value.casefold() in headers:
            continue
        seen.setdefault(normalize(value), value)
    return list(seen.values())


def has_header_value(row: RawRow, column_ids: list[str], headers: set[str]) -> bool:
    return any((row.cells.get(c) or "").strip().casefold() in headers for c in column_ids)


def match_person(name: str, people: list[Person]) -> tuple[Person | None, bool]:
    """Persona del directorio con el mismo nombre (sin tildes ni mayúsculas) y si es ambigua."""
    wanted = normalize(name).strip()
    found = [p for p in people if p.type is ShareType.USER and normalize(p.name or "") == wanted]
    if len(found) == 1:
        return found[0], False
    return None, len(found) > 1


@dataclass
class SheetLoad:
    """Acumulador de un diseñador en una hoja."""

    sheet_id: str
    sheet_name: str
    states: Counter[str] = field(default_factory=Counter)


@dataclass
class DesignerAccumulator:
    name: str
    phases: Counter[str] = field(default_factory=Counter)
    sheets: dict[str, SheetLoad] = field(default_factory=dict)

    def add(self, sheet_id: str, sheet_name: str, state: RowState, phase: str) -> None:
        load = self.sheets.setdefault(sheet_id, SheetLoad(sheet_id, sheet_name))
        load.states[state] += 1
        if state != "closed":
            self.phases[phase] += 1

    def total(self, state: RowState) -> int:
        return sum(load.states[state] for load in self.sheets.values())
