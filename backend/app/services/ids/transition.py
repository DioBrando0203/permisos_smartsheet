"""Valida consecutivos iniciales por ámbito; nunca los aprueba automáticamente."""

import json

from app.services.ids.formats import EntityKind, make_id


def standard_start(kind: EntityKind, parent: str) -> int:
    """Política vigente (2026-11-04): un ámbito sin rastro empieza en 1, en cualquier año.

    Un ámbito existente continúa desde su máximo registrado; nunca se reinicia ni reutiliza.
    """
    make_id(kind, parent, 1)
    return 1


def approved_starts(raw: str, *, approved: bool) -> dict[str, int]:
    """Devuelve sólo ámbitos canónicos explícitamente aprobados."""
    if not approved:
        return {}
    try:
        values = json.loads(raw)
    except (TypeError, ValueError):
        raise ValueError("Rangos iniciales inválidos") from None
    if not isinstance(values, dict):
        raise ValueError("Rangos iniciales inválidos")
    for scope, number in values.items():
        if not isinstance(scope, str) or not isinstance(number, int) or isinstance(number, bool):
            raise ValueError("Rangos iniciales inválidos")
        try:
            kind, parent = scope.split(":", 1)
            make_id(EntityKind(kind), parent, number)
        except ValueError:
            raise ValueError("Ámbito o consecutivo inicial inválido") from None
    return values
