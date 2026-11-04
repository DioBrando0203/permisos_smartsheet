"""Numeración hipotética en memoria; no reserva ni modifica PostgreSQL."""

from app.services.ids.formats import EntityKind, make_id
from app.services.ids.transition import standard_start


class Projector:
    def __init__(self, sequences: dict[str, int], used: set[str]) -> None:
        self._sequences = dict(sequences)
        self._used = set(used)

    def next(self, kind: EntityKind, parent: str) -> str:
        """Calcula un ejemplo no vinculante con la instantánea disponible."""
        scope = f"{kind.value}:{parent}"
        if standard_start(kind, parent, existing_scope=scope in self._sequences) is None:
            raise ValueError("Falta secuencia histórica para este ámbito")
        number = self._sequences.get(scope, 0)
        while True:
            number += 1
            value = make_id(kind, parent, number)
            if value not in self._used:
                break
        self._sequences[scope] = number
        self._used.add(value)
        return value
