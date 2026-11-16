"""Escrituras de estructura (columnas) del cliente de Smartsheet; barreras en el llamador."""

from app.core.config import Settings
from app.services.smartsheet.transport import Transport


class StructureWrites:
    """Mezcla de `SmartsheetClient`: usa su transporte y su configuración."""

    _settings: Settings
    _transport: Transport

    def _require_writes(self) -> None:
        from app.core.errors import AppError

        if self._settings.app_read_only:
            raise AppError("WRITE_BLOCKED", "Escrituras deshabilitadas (solo lectura).", 403)

    async def set_picklist_options(self, sheet_id: str, column_id: str, options: list[str]) -> None:
        """Reemplaza las opciones de un desplegable; no toca valores de celdas (ID-54)."""
        self._require_writes()
        await self._transport.request(
            "PUT",
            f"/sheets/{sheet_id}/columns/{column_id}",
            json={"type": "PICKLIST", "options": options},
            retry=False,
        )
