"""Procesa candidatos en orden de dependencia; sólo se activa con autorización explícita."""

import logging
from collections import Counter

import psycopg

from app.core.errors import AppError
from app.services.ids.connector import IdConnector, Target
from app.services.ids.formats import EntityKind

logger = logging.getLogger("app.ids")

_ELIGIBLE = frozenset(
    {"needs_reservation", "pending_formula", "would_write", "confirm_reservation"}
)
_ORDER = {"project": 0, "task": 1, "record": 2, "revision": 3}


async def process_report(
    connector: IdConnector,
    report: dict,
    *,
    limit: int | None = None,
    results: list[dict] | None = None,
) -> dict[str, int]:
    """Ejecuta secuencialmente candidatos válidos; aísla errores y conflictos por fila.

    `limit` acota las filas intentadas por ciclo; las restantes quedan como `deferred`.
    """
    counts: Counter[str] = Counter()
    items = sorted(
        report["pending_or_conflicting_rows"], key=lambda item: _ORDER.get(item["type"], 99)
    )
    attempted = 0
    for item in items:
        if item["action"] not in _ELIGIBLE or not item.get("parent"):
            continue
        if limit is not None and attempted >= limit:
            counts["deferred"] += 1
            continue
        attempted += 1
        try:
            target = Target(
                int(item["sheet_id"]), int(item["row_id"]), EntityKind(item["type"]), item["parent"]
            )
            outcome = (await connector.process(target)).value
        except (ValueError, RuntimeError, AppError, psycopg.Error):
            outcome = "error"
        counts[outcome] += 1
        # Sólo identificadores técnicos y resultado: nunca contenido de celdas ni personas.
        logger.info(
            "ids %s hoja %s fila %s -> %s", item["type"], item["sheet_id"], item["row_id"], outcome
        )
        if results is not None:
            results.append(
                {
                    "sheet_id": str(item["sheet_id"]),
                    "row_id": str(item["row_id"]),
                    "type": item["type"],
                    "outcome": outcome,
                }
            )
    return dict(counts)
