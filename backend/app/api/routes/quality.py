from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ServicesDep, SheetId
from app.models.quality import ColumnInfo, SheetQuality
from app.services.quality import QualityRequest

router = APIRouter()


@router.get("/{sheet_id}/columns")
async def sheet_columns(services: ServicesDep, sheet_id: SheetId) -> list[ColumnInfo]:
    """Columnas de la hoja (título, tipo, si es primaria) para elegir qué revisar."""
    return await services.quality.columns(sheet_id)


@router.get("/{sheet_id}/quality")
async def sheet_quality(
    services: ServicesDep,
    sheet_id: SheetId,
    unique: Annotated[
        list[str],
        Query(
            description="Columnas que no deben repetirse (título o id).",
            openapi_examples={"record_id": {"summary": "Record ID", "value": ["Record ID"]}},
        ),
    ] = [],  # noqa: B006 - FastAPI copia el valor por defecto en cada solicitud
    required: Annotated[
        list[str],
        Query(
            description="Columnas que no deben estar vacías.",
            openapi_examples={"designer": {"summary": "Designer1", "value": ["Designer1"]}},
        ),
    ] = [],  # noqa: B006
    pattern: Annotated[
        list[str],
        Query(
            description="Columna=expresión regular que debe cumplir cada valor no vacío.",
            openapi_examples={
                "record_id": {"summary": "Record ID numérico", "value": ["Record ID=^\\d+$"]}
            },
        ),
    ] = [],  # noqa: B006
    refresh: bool = False,
) -> SheetQuality:
    """Identificadores repetidos o mal formados y filas sin un dato obligatorio. Sólo lectura."""
    request = QualityRequest(unique=unique, required=required, patterns=pattern)
    return await services.quality.check(sheet_id, request, refresh=refresh)
