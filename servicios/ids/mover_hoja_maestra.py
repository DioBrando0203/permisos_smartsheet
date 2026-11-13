"""Traslada el registro de IDs y Obs a otra hoja maestra (PEN-48); no escribe en Smartsheet.

Uso, con el backend detenido y desde `backend`:
`.venv/bin/python ../servicios/ids/mover_hoja_maestra.py --destino ID [--origen ID] [--confirmar]`.
Sin `--confirmar` sólo muestra el plan. Con `--confirmar` respalda en `~/galp_backups` las
asignaciones que mueve y aplica todo en una transacción. Después se fija `IDS_MASTER_SHEET_ID`
en `backend/.env` y se arranca el backend.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import psycopg  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.services.ids.cli import DSN  # noqa: E402
from app.services.ids.dry_run import PILOT_WORKSPACE  # noqa: E402
from app.services.ids.rehome import apply_moves, plan_moves  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402

STABLE = "Stable Tracking Project"


async def mothers(client: SmartsheetClient, sheet: str) -> list[tuple[str, int]]:
    if await client.sheet_workspace_id(sheet) != PILOT_WORKSPACE:
        raise SystemExit(f"La hoja {sheet} no está en Pruebas: no se toca")
    column = [c.id for c in await client.list_columns(sheet) if c.title == STABLE]
    if len(column) != 1:
        raise SystemExit(f"La hoja {sheet} no tiene una sola columna {STABLE}")
    rows = await client.list_rows(sheet, column)
    return [
        ((row.cells.get(column[0]) or "").strip(), int(row.id))
        for row in rows
        if not row.parent_id and (row.cells.get(column[0]) or "").strip()
    ]


async def main(args: argparse.Namespace) -> None:
    client = SmartsheetClient(Settings())
    try:
        origin = await mothers(client, args.origen)
        destination = await mothers(client, args.destino)
        comments = [
            (int(c.id), int(c.row_id)) for c in await client.list_row_comments(args.destino)
        ]
    finally:
        await client.aclose()
    with psycopg.connect(DSN, options="-c default_transaction_read_only=on") as conn:
        registered = dict(
            conn.execute(
                "SELECT id_generado, fila_id FROM asignacion_id WHERE hoja_id=%s",
                (int(args.origen),),
            ).fetchall()
        )
        taken = conn.execute(
            "SELECT count(*) FROM asignacion_id WHERE hoja_id=%s", (int(args.destino),)
        ).fetchone()[0]
    if taken:
        raise SystemExit(f"La copia ya tiene {taken} asignaciones: revisar antes de seguir")
    moves = plan_moves(registered, origin, destination)
    print(
        f"Madres con ID: origen {len(origin)}, copia {len(destination)}; se trasladan {len(moves)}."
    )
    print("IDs:", ", ".join(move.value for move in moves))
    print(f"Comentarios de la copia que se marcan como ya copiados a Obs: {len(comments)}.")
    print(f"Asignaciones que siguen en la hoja de origen: {len(registered) - len(moves)}.")
    if not args.confirmar:
        print("Simulación: nada cambió. Repetir con --confirmar.")
        return
    backups = Path.home() / "galp_backups"
    backups.mkdir(mode=0o700, exist_ok=True)
    backup = backups / f"mover_hoja_{datetime.now():%Y%m%d_%H%M%S}.json"
    plan = {"origen": args.origen, "destino": args.destino, "moves": [m.__dict__ for m in moves]}
    backup.write_text(json.dumps(plan, indent=1))
    apply_moves(DSN, int(args.origen), int(args.destino), moves, comments)
    print(f"Hecho. Respaldo del plan: {backup}. Fijar IDS_MASTER_SHEET_ID={args.destino}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--origen", default="5254686035890052")
    parser.add_argument("--destino", required=True)
    parser.add_argument("--confirmar", action="store_true")
    asyncio.run(main(parser.parse_args()))
