"""Ensambla el coordinador real sólo si todas las barreras de escritura están activas."""

from collections.abc import Callable

from app.core.config import Settings
from app.services.ids.cli import DSN
from app.services.ids.connector import IdConnector
from app.services.ids.gateway import SmartsheetIdGateway
from app.services.ids.store import IdStore
from app.services.ids.transition import approved_starts
from app.services.smartsheet import SmartsheetClient


def write_barriers(settings: Settings) -> dict[str, bool]:
    """Cada barrera por separado; la escritura exige todas en verdadero."""
    return {
        "app_read_only_disabled": not settings.app_read_only,
        "ids_writes_enabled": settings.ids_writes_enabled,
        "ids_transition_approved": settings.ids_transition_approved,
    }


def writes_allowed(settings: Settings) -> bool:
    return all(write_barriers(settings).values())


def build_store(settings: Settings, dsn: str = DSN) -> IdStore:
    """Reservas habilitadas sólo con escritura permitida y política aprobada."""
    if not writes_allowed(settings):
        raise ValueError("Escritura de IDs deshabilitada")
    starts = approved_starts(
        settings.ids_approved_starts, approved=settings.ids_transition_approved
    )
    return IdStore(
        dsn,
        allow_reservations=True,
        approved_starts=starts,
        annual_policy_approved=settings.ids_transition_approved,
    )


def build_connector(settings: Settings, client: SmartsheetClient, store: IdStore) -> IdConnector:
    return IdConnector(store, SmartsheetIdGateway(client, store), read_only=settings.app_read_only)


def assign_factory(
    settings: Settings, client: SmartsheetClient, dsn: str = DSN
) -> Callable[[], IdConnector] | None:
    """Coordinador para el procesador; None mantiene el procesador en simulación."""
    if not settings.ids_processor_writes_enabled or not writes_allowed(settings):
        return None
    return lambda: build_connector(settings, client, build_store(settings, dsn))
