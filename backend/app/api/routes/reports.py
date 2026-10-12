from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import (
    EXAMPLE_PREVIOUS_SHEET_ID,
    EXAMPLE_SHEET_ID,
    ServicesDep,
    SheetId,
)
from app.models.reports import AccessSummary, SheetAudit, SheetComparison

router = APIRouter()

_SHEET_REF = r"^[A-Za-z0-9]{1,64}$"
SheetA = Annotated[
    str,
    Query(
        pattern=_SHEET_REF,
        description="Hoja A: id o código del permalink.",
        openapi_examples={
            "plan_2025": {"summary": "Plan 2025", "value": EXAMPLE_PREVIOUS_SHEET_ID}
        },
    ),
]
SheetB = Annotated[
    str,
    Query(
        pattern=_SHEET_REF,
        description="Hoja B: id o código del permalink.",
        openapi_examples={"plan_2026": {"summary": "Plan 2026", "value": EXAMPLE_SHEET_ID}},
    ),
]


@router.get("/compare")
async def compare_sheets(services: ServicesDep, a: SheetA, b: SheetB) -> SheetComparison:
    """Quién está sólo en A, sólo en B y quién tiene distinto nivel (nivel efectivo)."""
    sheet_a = await services.sheets.resolve_id(a)
    sheet_b = await services.sheets.resolve_id(b)
    return await services.reports.compare(sheet_a, sheet_b)


@router.get("/access-summary")
async def access_summary(
    services: ServicesDep,
    q: Annotated[
        str | None,
        Query(
            openapi_examples={"crown": {"summary": "Planes Crown Castle", "value": "crown castle"}}
        ),
    ] = None,
    inactive_days: Annotated[int | None, Query(ge=1, le=3650)] = None,
    refresh: bool = False,
) -> AccessSummary:
    """Cuánta gente conserva acceso a cada hoja; `inactive_days` marca las sin cambios."""
    return await services.reports.access_summary(q, inactive_days, refresh=refresh)


@router.get("/{sheet_id}/audit")
async def audit_sheet(
    services: ServicesDep, sheet_id: SheetId, refresh: bool = False
) -> SheetAudit:
    """Resumen de quién tiene acceso y alertas: externos que comparten, correos personales…"""
    return await services.reports.audit(sheet_id, refresh=refresh)
