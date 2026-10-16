from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ServicesDep, SheetId
from app.models.quality import AccountReferences, SheetReferences

router = APIRouter()

# Catálogo real de la cuenta usado como ejemplo en Swagger: "Source Designers".
_CATALOG_EXAMPLE = {"designers": {"summary": "Source Designers", "value": "4315680049418116"}}
Column = Annotated[
    str,
    Query(
        description="Columna a revisar (título o id).",
        openapi_examples={"designer": {"summary": "Designer1", "value": "Designer1"}},
    ),
]
CatalogSheet = Annotated[
    str,
    Query(
        pattern=r"^[A-Za-z0-9]{1,64}$",
        description="Hoja catálogo: id o código del permalink.",
        openapi_examples=_CATALOG_EXAMPLE,
    ),
]
CatalogColumn = Annotated[
    str,
    Query(
        description="Columna del catálogo con los valores válidos.",
        openapi_examples={"designer": {"summary": "Designer", "value": "Designer"}},
    ),
]


@router.get("/sheets/{sheet_id}/references")
async def sheet_references(
    services: ServicesDep,
    sheet_id: SheetId,
    column: Column,
    catalog_sheet: CatalogSheet,
    catalog_column: CatalogColumn,
    refresh: bool = False,
) -> SheetReferences:
    """Valores de `column` que no están en el catálogo (por ejemplo, diseñadores desconocidos)."""
    return await services.references.sheet(
        sheet_id, column, catalog_sheet, catalog_column, refresh=refresh
    )


@router.get("/references")
async def account_references(
    services: ServicesDep,
    column: Column,
    catalog_sheet: CatalogSheet,
    catalog_column: CatalogColumn,
    q: str | None = None,
    refresh: bool = False,
) -> AccountReferences:
    """La misma revisión en todas las hojas que tienen `column`; qué valor falta en más hojas."""
    return await services.references.account(
        column, catalog_sheet, catalog_column, q, refresh=refresh
    )
