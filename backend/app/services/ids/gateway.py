"""Adaptador de Smartsheet para IDs; la comprobación previa no es atómica."""

import asyncio

from app.core.errors import AppError
from app.services.ids.connector import Snapshot, Target, WriteUncertain
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.ids.formats import EntityKind, parse_id, project_scope
from app.services.ids.pilot import SHEETS
from app.services.ids.store import IdStore
from app.services.smartsheet import RawRow, SmartsheetClient


class SmartsheetIdGateway:
    def __init__(self, client: SmartsheetClient, store: IdStore) -> None:
        self._client = client
        self._store = store

    async def read(self, target: Target) -> Snapshot:
        spec = next((item for item in SHEETS if item[0] == str(target.sheet_id)), None)
        if spec is None or spec[1] != target.kind:
            return Snapshot(None, "", False, "", "")
        sheet_id = str(target.sheet_id)
        workspace = await self._client.sheet_workspace_id(sheet_id)
        if workspace != PILOT_WORKSPACE:
            return Snapshot(workspace, "", False, "", "")
        columns = await self._client.list_columns(sheet_id)
        by_title = {column.title: column.id for column in columns}
        if len(by_title) != len(columns) or spec[2] not in by_title or spec[3] not in by_title:
            raise ValueError("Columnas del piloto inválidas")
        row = await self._client.get_row(sheet_id, str(target.row_id))
        visible = (row.cells.get(by_title[spec[2]]) or "").strip()
        stable = (row.cells.get(by_title[spec[3]]) or "").strip()
        parent = target.parent
        if spec[4]:
            if spec[4] not in by_title:
                raise ValueError("Columna de referencia ausente")
            parent = (row.cells.get(by_title[spec[4]]) or "").strip()
            if target.kind == EntityKind.TASK:
                reference = (row.cells.get(by_title.get("Reference", "")) or "").strip()
                if reference != parent:
                    return Snapshot(workspace, "", False, visible, stable)
        else:
            parent = _project_scope(row, by_title)
            if visible:
                try:
                    if parse_id(target.kind, visible).parent != parent:
                        parent = ""
                except ValueError:
                    parent = ""
        confirmed = target.kind == EntityKind.PROJECT or await self._parent_confirmed(
            target, parent
        )
        return Snapshot(workspace, parent, confirmed, visible, stable)

    async def _parent_confirmed(self, target: Target, value: str) -> bool:
        parent_sheet = 4365321059389316 if target.kind == EntityKind.TASK else 73093952524164
        row_id = await asyncio.to_thread(self._store.confirmed_parent, parent_sheet, value)
        if (
            row_id is None
            or await self._client.sheet_workspace_id(str(parent_sheet)) != PILOT_WORKSPACE
        ):
            return False
        title = "Stable Tracking Project" if target.kind == EntityKind.TASK else "Stable Task ID"
        columns = await self._client.list_columns(str(parent_sheet))
        ids = [column.id for column in columns if column.title == title]
        if len(ids) != 1:
            return False
        row = await self._client.get_row(str(parent_sheet), str(row_id))
        return (row.cells.get(ids[0]) or "").strip() == value

    async def write_if_unchanged(self, target: Target, previous: Snapshot, value: str) -> bool:
        """Relee antes de escribir; una edición externa simultánea todavía puede competir."""
        if previous.stable or await self.read(target) != previous:
            return False
        try:
            await self._client.update_stable_id_once(
                str(target.sheet_id), str(target.row_id), value
            )
        except AppError as error:
            if error.code == "IDS_STABLE_EXISTS":
                return False
            if error.status >= 500:
                raise WriteUncertain() from None
            raise
        return True


def _project_scope(row: RawRow, columns: dict[str, str]) -> str:
    """Obtiene el año del valor ISO de Date Received, no de su texto localizado."""
    company = (row.cells.get(columns.get("KMV/GALP", "")) or "").strip()
    customer = (row.cells.get(columns.get("Customer Code", "")) or "").strip()
    received = row.date_cells.get(columns.get("Date Received", ""))
    return project_scope(company, customer, received)
