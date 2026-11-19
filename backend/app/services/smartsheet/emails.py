"""Envío de filas por correo desde Smartsheet (SPEC-B19 FH-05c), mezcla del cliente."""

from app.core.config import Settings
from app.services.smartsheet.transport import Transport


class EmailWrites:
    """Mezcla de `SmartsheetClient`: usa su transporte y su configuración."""

    _settings: Settings
    _transport: Transport

    async def send_rows_email(
        self,
        sheet_id: str,
        row_ids: list[str],
        recipients: list[str],
        subject: str,
        message: str,
        column_ids: list[str],
    ) -> None:
        """Smartsheet manda las filas con ese mensaje; no escribe nada en la hoja."""
        from app.core.errors import AppError

        if self._settings.app_read_only:
            raise AppError("WRITE_BLOCKED", "Escrituras deshabilitadas (solo lectura).", 403)
        body = {
            "sendTo": [{"email": email} for email in recipients],
            "subject": subject,
            "message": message,
            "ccMe": False,
            "rowIds": [int(row) for row in row_ids],
            "columnIds": [int(column) for column in column_ids],
            "includeAttachments": False,
            "includeDiscussions": False,
            "layout": "VERTICAL",
        }
        await self._transport.request(
            "POST", f"/sheets/{sheet_id}/rows/emails", json=body, retry=False
        )
