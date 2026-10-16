from datetime import datetime

from pydantic import BaseModel

from app.services.permissions import AccessLevel


class SheetSummary(BaseModel):
    id: str
    name: str
    # None: hoja de otra persona de la organización, no compartida con el token (PEN-14).
    access_level: AccessLevel | None = None
    can_manage_shares: bool
    permalink: str | None = None
    modified_at: datetime | None = None
    # Marcada a mano: hay gente que puede verla por Dynamic View sin figurar en sus permisos.
    has_dynamic_view: bool = False
    owner_email: str | None = None
    # False: sólo se consulta; Smartsheet no deja abrirla ni escribir con este token.
    in_my_list: bool = True


class SheetList(BaseModel):
    sheets: list[SheetSummary]
    total: int
    total_mine: int
    loaded_at: datetime | None = None
