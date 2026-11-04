"""Prueba manual de una fila designada; bloqueada sin aprobación y configuración explícitas."""

import argparse
import asyncio

from app.core.config import Settings
from app.services.ids.cli import DSN
from app.services.ids.connector import IdConnector, Target
from app.services.ids.formats import EntityKind
from app.services.ids.gateway import SmartsheetIdGateway
from app.services.ids.pilot import SHEETS
from app.services.ids.store import IdStore
from app.services.ids.transition import approved_starts
from app.services.smartsheet import SmartsheetClient


async def execute(sheet_id: int, row_id: int, parent: str, authorized: bool) -> str:
    """Procesa sólo la fila indicada después de comprobar barreras de activación."""
    settings = Settings()
    if (
        not authorized
        or settings.app_read_only
        or not settings.ids_writes_enabled
        or not settings.ids_transition_approved
    ):
        raise ValueError("Prueba real no autorizada o escritura deshabilitada")
    # PEN-08 exige identidad OAuth antes de habilitar escrituras con la cuenta administradora.
    raise ValueError("Prueba real bloqueada: OAuth aún no está implementado")
    spec = next((item for item in SHEETS if item[0] == str(sheet_id)), None)
    if spec is None or row_id <= 0:
        raise ValueError("Hoja o fila no autorizada")
    starts = approved_starts(
        settings.ids_approved_starts, approved=settings.ids_transition_approved
    )
    store = IdStore(
        DSN,
        allow_reservations=True,
        approved_starts=starts,
        annual_policy_approved=settings.ids_transition_approved,
    )
    existing = await asyncio.to_thread(store.lookup, sheet_id, row_id)
    if existing and not await asyncio.to_thread(store.is_service_reservation, sheet_id, row_id):
        raise ValueError("La fila corresponde a un ID importado; no es una prueba desechable")
    client = SmartsheetClient(settings)
    try:
        gateway = SmartsheetIdGateway(client, store)
        connector = IdConnector(store, gateway, read_only=settings.app_read_only)
        return (
            await connector.process(Target(sheet_id, row_id, EntityKind(spec[1]), parent))
        ).value
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
