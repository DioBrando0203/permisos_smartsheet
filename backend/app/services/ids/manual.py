"""Prueba manual de una fila designada; bloqueada sin aprobación y configuración explícitas."""

import argparse
import asyncio

from app.core.config import Settings
from app.services.ids import pilot
from app.services.ids.cli import DSN
from app.services.ids.connector import Target
from app.services.ids.formats import EntityKind
from app.services.ids.runtime import build_connector, build_store, writes_allowed
from app.services.smartsheet import SmartsheetClient


def _check(settings: Settings, authorized: bool) -> None:
    # Por decisión del usuario (2026-11-04) el piloto usa el token máquina a máquina, sin OAuth.
    if not authorized or not writes_allowed(settings):
        raise ValueError("Prueba real no autorizada o escritura deshabilitada")


async def assign_row(
    settings: Settings,
    client: SmartsheetClient,
    dsn: str,
    target: tuple[int, int, str],
    authorized: bool,
) -> dict:
    """Procesa sólo la fila indicada (hoja, fila, padre) después de comprobar las barreras."""
    _check(settings, authorized)
    sheet_id, row_id, parent = target
    spec = pilot.sheet_spec(sheet_id)
    if spec is None or row_id <= 0 or not parent.strip():
        raise ValueError("Hoja, fila o padre no autorizados")
    store = build_store(settings, dsn)
    existing = await asyncio.to_thread(store.lookup, sheet_id, row_id)
    if existing and not await asyncio.to_thread(store.is_service_reservation, sheet_id, row_id):
        raise ValueError("La fila corresponde a un ID importado; no es una prueba desechable")
    connector = build_connector(settings, client, store)
    outcome = await connector.process(Target(sheet_id, row_id, EntityKind(spec[1]), parent.strip()))
    reservation = await asyncio.to_thread(store.lookup, sheet_id, row_id)
    return {
        "sheet_id": str(sheet_id),
        "row_id": str(row_id),
        "outcome": outcome.value,
        "id": reservation.value if reservation else None,
        "state": reservation.state if reservation else None,
    }


async def execute(sheet_id: int, row_id: int, parent: str, authorized: bool) -> dict:
    """Variante de consola: comprueba barreras antes de abrir el cliente."""
    settings = Settings()
    _check(settings, authorized)
    client = SmartsheetClient(settings)
    try:
        return await assign_row(settings, client, DSN, (sheet_id, row_id, parent), authorized)
    finally:
        await client.aclose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba de una fila designada del piloto")
    parser.add_argument("--sheet-id", type=int, required=True)
    parser.add_argument("--row-id", type=int, required=True)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--authorize-test-write", action="store_true")
    args = parser.parse_args()
    print(asyncio.run(execute(args.sheet_id, args.row_id, args.parent, args.authorize_test_write)))


if __name__ == "__main__":
    main()
