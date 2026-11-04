"""Procesa candidatos en orden de dependencia; sólo se activa con autorización explícita."""

from collections import Counter

import psycopg

from app.core.errors import AppError
from app.services.ids.connector import IdConnector, Target
from app.services.ids.formats import EntityKind

_ELIGIBLE = frozenset(
    {"needs_reservation", "pending_formula", "would_write", "confirm_reservation"}
)


async def process_report(connector: IdConnector, report: dict) -> dict[str, int]:
    """Ejecuta secuencialmente candidatos válidos; aísla conflictos por fila."""
    counts: Counter[str] = Counter()
    order = {"project": 0, "task": 1, "record": 2, "revision": 3}
    items = sorted(
        report["pending_or_conflicting_rows"], key=lambda item: order.get(item["type"], 99)
    )
    for item in items:
        if item["action"] not in _ELIGIBLE or not item.get("parent"):
            continue
        try:
            target = Target(
                int(item["sheet_id"]), int(item["row_id"]), EntityKind(item["type"]), item["parent"]
            )
            result = await connector.process(target)
            counts[result.value] += 1
        except (ValueError, RuntimeError, AppError, psycopg.Error):
            counts["error"] += 1
    return dict(counts)
