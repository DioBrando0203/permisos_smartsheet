"""Numeración hipotética en memoria; no reserva ni modifica PostgreSQL."""

from app.services.ids.formats import EntityKind, make_id, parse_id
from app.services.ids.transition import standard_start


class Projector:
    def __init__(self, sequences: dict[str, int], used: set[str]) -> None:
        self._sequences = dict(sequences)
        self._used = set(used)

    def register(self, kind: EntityKind, value: str) -> None:
        """Un Stable ID sin rastro se registrará tal cual: ocupa su número en la proyección."""
        try:
            parts = parse_id(kind, value)
        except ValueError:
            return
        current = self._sequences.get(parts.scope, 0)
        self._sequences[parts.scope] = max(current, parts.number)
        self._used.add(value)

    def next(self, kind: EntityKind, parent: str, preferred: int | None = None) -> str:
        """Ejemplo no vinculante: adopta el número de la fórmula si supera el máximo registrado."""
        scope = f"{kind.value}:{parent}"
        current = self._sequences.get(scope, 0)
        start = standard_start(kind, parent)
        if preferred is not None and preferred > current and preferred >= start:
            number = preferred
            value = make_id(kind, parent, number)
        else:
            number = max(current, start - 1)
            while True:
                number += 1
                value = make_id(kind, parent, number)
                if value not in self._used:
                    break
        self._sequences[scope] = number
        self._used.add(value)
        return value
