"""Reporte de simulación de IDs para Swagger."""

import asyncio
from collections import Counter

import psycopg

from app.services.ids.dry_run import (
    PILOT_WORKSPACE,
    Candidate,
    PlanAction,
    plan,
)
from app.services.ids.formats import EntityKind, parse_id, project_scope
from app.services.ids.pilot import SHEETS, read_pilot
from app.services.ids.simulation import Projector
from app.services.smartsheet import SmartsheetClient


def _db_snapshot(dsn: str) -> tuple[dict, dict]:
    """Consultar reservas y secuencias sin modificar PostgreSQL."""

    with psycopg.connect(
        dsn,
        connect_timeout=5,
        options="-c default_transaction_read_only=on",
    ) as conn:
        reservations = {
            (int(sheet_id), int(row_id)): (value, state)
            for sheet_id, row_id, value, state in conn.execute(
                "SELECT hoja_id, fila_id, id_generado, estado FROM asignacion_id"
            ).fetchall()
        }

        sequences = dict(conn.execute("SELECT ambito, ultimo_numero FROM secuencia_id").fetchall())

    return reservations, sequences


async def build_dry_run_report(
    client: SmartsheetClient,
    dsn: str,
) -> dict:
    """Generar un reporte sin reservar ni escribir IDs."""

    sheets = await read_pilot(client)

    reservations, sequences = await asyncio.to_thread(
        _db_snapshot,
        dsn,
    )

    confirmed: set[str] = set()

    projector = Projector(
        sequences,
        {value for value, _ in reservations.values()},
    )

    allowed = frozenset(sheet_id for sheet_id, *_ in SHEETS)

    counts = Counter()
    details = []

    for sheet in sheets:
        for row in sheet.rows:
            visible = (row.cells.get(sheet.visible_column) or "").strip()

            stable = (row.cells.get(sheet.stable_column) or "").strip()

            parent = (
                (row.cells.get(sheet.parent_column) or "").strip() if sheet.parent_column else ""
            )

            if sheet.kind == EntityKind.PROJECT and sheet.project_columns:
                company, customer, received = sheet.project_columns
                parent = project_scope(
                    row.cells.get(company) or "",
                    row.cells.get(customer) or "",
                    row.date_cells.get(received),
                )
            elif sheet.kind == EntityKind.PROJECT and visible:
                try:
                    parent = parse_id(
                        sheet.kind,
                        visible,
                    ).parent

                except ValueError:
                    pass

            if not visible and not stable and not parent:
                continue

            reservation = reservations.get((sheet.sheet_id, int(row.id)))

            extra_parent_conflict = bool(
                sheet.extra_parent_column
                and parent
                and (row.cells.get(sheet.extra_parent_column) or "").strip() != parent
            )

            candidate = Candidate(
                str(sheet.sheet_id),
                PILOT_WORKSPACE,
                sheet.kind,
                parent,
                sheet.kind == EntityKind.PROJECT or parent in confirmed,
                visible,
                stable,
                reservation[0] if reservation else None,
                reservation[1] if reservation else None,
            )

            action = PlanAction.CONFLICT if extra_parent_conflict else plan(candidate, allowed)

            proposed = None

            if (
                action
                in (
                    PlanAction.NEEDS_RESERVATION,
                    PlanAction.PENDING_FORMULA,
                )
                and parent
            ):
                try:
                    proposed = reservation[0] if reservation else projector.next(sheet.kind, parent)
                except ValueError:
                    action = PlanAction.CONFLICT
                if visible and proposed and proposed != visible:
                    action = PlanAction.CONFLICT

            counts[action.value] += 1

            if action == PlanAction.ALREADY_STABLE and reservation == (stable, "confirmado"):
                confirmed.add(stable)

            if action != PlanAction.ALREADY_STABLE:
                details.append(
                    {
                        "sheet_id": str(sheet.sheet_id),
                        "row_id": str(row.id),
                        "type": sheet.kind.value,
                        "parent": parent,
                        "action": action.value,
                        "visible_id": visible,
                        "stable_id": stable,
                        "proposed_id": proposed,
                    }
                )

    return {
        "mode": "dry_run",
        "read_only": True,
        "counts": dict(counts),
        "pending_or_conflicting_rows": details,
        "warning": ("Estimaciones orientativas. No reservan IDs ni garantizan máximos históricos."),
    }
