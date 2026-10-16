from dataclasses import replace
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ServicesDep
from app.models.designers import DesignerWorkload

router = APIRouter()


@router.get("/designers")
async def designer_workload(
    services: ServicesDep,
    q: Annotated[
        str | None,
        Query(
            description="Filtra hojas por nombre.",
            openapi_examples={"plans": {"summary": "Planes de ingeniería", "value": "plan"}},
        ),
    ] = None,
    designer_columns: Annotated[
        list[str] | None, Query(description="Por defecto APP_DESIGNER_COLUMNS.")
    ] = None,
    status_column: Annotated[
        str | None, Query(description="Por defecto APP_STATUS_COLUMN.")
    ] = None,
    closed_status: Annotated[
        list[str] | None, Query(description="Estados cerrados; por defecto APP_CLOSED_STATUSES.")
    ] = None,
    refresh: bool = False,
) -> DesignerWorkload:
    """Trabajo abierto, en espera y cerrado de cada diseñador en todas las hojas.

    Cruza cada asignación con los permisos: `sheets_without_access` cuenta hojas donde el
    diseñador tiene trabajo abierto pero no la tiene compartida.
    """
    request = services.designers.default_request(q)
    request = replace(
        request,
        designer_columns=designer_columns or request.designer_columns,
        status_column=status_column or request.status_column,
        closed_statuses=closed_status or request.closed_statuses,
    )
    return await services.designers.workload(request, refresh=refresh)
