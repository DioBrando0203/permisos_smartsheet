"""Exportación a CSV de quién tiene acceso a qué hoja (PEN-12). Sólo lectura.

Se genera en memoria bajo demanda y no se guarda en el servidor: contiene correos reales.
Pensado para abrirse con doble clic en Excel en español: `;` y UTF-8 con BOM.
"""

import asyncio
import csv
import io

from app.models.people import FailedSheet
from app.services.directory import SheetShares, person_key
from app.services.people import PeopleService
from app.services.permissions import LABELS, ShareScope, ShareType, lock_reason
from app.services.sheets import SheetScope, SheetService
from app.services.smartsheet import RawShare

HEADER = [
    "Hoja",
    "Id hoja",
    "Dueño de la hoja",
    "Compartida con el token",
    "Tipo",
    "Nombre",
    "Correo o grupo",
    "Nivel",
    "Nivel (código)",
    "Origen",
    "Editable desde el panel",
    "Usuario de la organización",
    "En contactos",
]
# Excel ejecuta como fórmula un valor que empieza así (inyección de CSV).
_BOM = "\N{ZERO WIDTH NO-BREAK SPACE}"  # U+FEFF, marca de UTF-8 para Excel
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class ExportService:
    def __init__(self, sheets: SheetService, people: PeopleService) -> None:
        self._sheets = sheets
        self._people = people

    async def access_csv(
        self, query: str | None, scope: SheetScope
    ) -> tuple[str, list[FailedSheet]]:
        all_sheets = await self._sheets.raw_sheets()
        listed = await self._sheets.list(query, scope)
        wanted = {summary.id for summary in listed.sheets}
        sheets = [sheet for sheet in all_sheets if sheet.id in wanted]
        results = await asyncio.gather(*(self._people.sheet_shares(sheet) for sheet in sheets))
        org = {user.email for user in await self._people.raw_org_users() or []}
        contacts = {contact.email for contact in await self._people.raw_contacts()}
        loaded = [item for item in results if isinstance(item, SheetShares)]
        failed = [item for item in results if isinstance(item, FailedSheet)]
        return render(loaded, org, contacts), failed


def render(items: list[SheetShares], org: set[str], contacts: set[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(HEADER)
    for item in sorted(items, key=lambda entry: entry.sheet.name.casefold()):
        for share in item.shares:
            writer.writerow([_safe(value) for value in _row(item, share, org, contacts)])
    # BOM: sin él, Excel abre el UTF-8 como ANSI y rompe las tildes.
    return _BOM + buffer.getvalue()


def _row(item: SheetShares, share: RawShare, org: set[str], contacts: set[str]) -> list[str]:
    sheet = item.sheet
    is_group = share.type is ShareType.GROUP
    item_id = share.group_id if is_group else share.user_id
    reason = lock_reason(share.access_level, share.scope, sheet.access_level)
    return [
        sheet.name,
        sheet.id,
        sheet.owner_email or "",
        _yes(sheet.in_my_list),
        "Grupo" if is_group else "Usuario",
        share.name or "",
        share.email or person_key(share.type, share.email, item_id),
        LABELS[share.access_level],
        str(share.access_level),
        "Heredado del workspace" if share.scope is ShareScope.WORKSPACE else "Propio",
        _yes(reason is None),
        "" if is_group else _yes(share.email in org),
        "" if is_group else _yes(share.email in contacts),
    ]


def _yes(value: bool) -> str:
    return "Sí" if value else "No"


def _safe(value: str) -> str:
    return f"'{value}" if value.startswith(_FORMULA_PREFIXES) else value
