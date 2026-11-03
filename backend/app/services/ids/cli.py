"""Herramienta manual para importar el piloto o simular; nunca escribe en Smartsheet."""

import argparse
import asyncio
from collections import Counter
from pathlib import Path

import psycopg

from app.core.config import Settings
from app.services.ids.dry_run import Candidate, plan
from app.services.ids.formats import EntityKind, parse_id
from app.services.ids.inventory import collect_inventory
from app.services.ids.pilot import SHEETS, read_pilot
from app.services.ids.simulation import Projector
from app.services.ids.store import IdStore
from app.services.smartsheet import SmartsheetClient

DSN = psycopg.conninfo.make_conninfo(
    host="127.0.0.1",
    dbname="galp_servicios",
    user="galp_ids",
    passfile=str(Path.home() / ".config" / "galp_servicios" / "pgpass"),
)


async def run(action: str) -> None:
    """Lee el piloto y ejecuta sólo la operación local solicitada."""
    settings = Settings()
    if not settings.app_read_only:
        raise ValueError("Se requiere APP_READ_ONLY=true")
    client = SmartsheetClient(settings)
    try:
        sheets = await read_pilot(client)
        entries = collect_inventory(sheets, ignore_pending=action == "dry-run")
        if action == "importar":
            IdStore(DSN).initialize(entries)
            print(f"Inventario importado o ya coincidente: {len(entries)} IDs.")
        else:
            await _simulate(sheets, entries)
    finally:
        await client.aclose()


async def _simulate(sheets, entries) -> None:
    # Conexión de sólo lectura, sin reservar números ni alterar secuencias.
    print("Simulación orientativa: historial incompleto, no autoriza reservas ni escrituras.")
    with psycopg.connect(DSN, options="-c default_transaction_read_only=on") as conn:
        reservations = {
            (sheet_id, row_id): (value, state)
            for sheet_id, row_id, value, state in conn.execute(
                "SELECT hoja_id, fila_id, id_generado, estado FROM asignacion_id"
            ).fetchall()
        }
        sequences = dict(conn.execute("SELECT ambito, ultimo_numero FROM secuencia_id").fetchall())
    projector = Projector(sequences, {value for value, _ in reservations.values()})
    valid_ids = {
        entry.value
        for entry in entries
        if reservations.get((entry.sheet_id, entry.row_id)) == (entry.value, "confirmado")
    }
    allowed = frozenset(item[0] for item in SHEETS)
    counts = Counter()
    for sheet in sheets:
        for row in sheet.rows:
            visible = (row.cells.get(sheet.visible_column) or "").strip()
            stable = (row.cells.get(sheet.stable_column) or "").strip()
            parent = (
                (row.cells.get(sheet.parent_column) or "").strip() if sheet.parent_column else ""
            )
            if not visible and not stable and not parent:
                continue
            if sheet.extra_parent_column and parent:
                reference = (row.cells.get(sheet.extra_parent_column) or "").strip()
                if reference != parent:
                    counts["conflict"] += 1
                    print(f"Hoja {sheet.sheet_id}, fila {row.id}: conflict")
                    continue
            if sheet.kind == EntityKind.PROJECT and visible:
                try:
                    parent = parse_id(sheet.kind, visible).parent
                except ValueError:
                    pass
            reservation = reservations.get((sheet.sheet_id, int(row.id)))
            candidate = Candidate(
                str(sheet.sheet_id),
                "7965022790936452",
                sheet.kind,
                parent,
                sheet.kind == EntityKind.PROJECT or parent in valid_ids,
                visible,
                stable,
                reservation[0] if reservation else None,
                reservation[1] if reservation else None,
            )
            action = plan(candidate, allowed)
            counts[action.value] += 1
            if action.value in ("needs_reservation", "pending_formula") and parent:
                example = reservation[0] if reservation else projector.next(sheet.kind, parent)
                if visible and example != visible:
                    counts[action.value] -= 1
                    counts["conflict"] += 1
                print(
                    f"Hoja {sheet.sheet_id}, fila {row.id}: estimado {example}; "
                    f"fórmula {visible or '(pendiente)'}; "
                    f"coinciden: {example == visible if visible else 'pendiente'}"
                )
                continue
            if action.value not in ("already_stable", "confirm_reservation"):
                print(f"Hoja {sheet.sheet_id}, fila {row.id}: {action.value}")
    print("Simulación sin escrituras:", dict(counts))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa o simula IDs del piloto sin escribir Smartsheet"
    )
    parser.add_argument("accion", choices=("importar", "dry-run"))
    args = parser.parse_args()
    asyncio.run(run(args.accion))


if __name__ == "__main__":
    main()
