"""Registro del servicio y consumo de API, con la autenticación del ID Manager (SPEC-B21 RG-02).

Sólo lee lo que ya está en memoria: no llama a Smartsheet ni a PostgreSQL.
"""

from dataclasses import asdict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import ServicesDep
from app.api.routes.idsmart import require_admin
from app.models.logs import ApiUsageOut, LogEntryOut, LogsResponse

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/logs", summary="Eventos recientes del servicio y consumo de API")
async def get_logs(
    request: Request,
    services: ServicesDep,
    level: Literal["INFO", "WARNING", "ERROR"] = "WARNING",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    contains: Annotated[str, Query(max_length=200)] = "",
) -> LogsResponse:
    book = request.app.state.logbook
    items = [LogEntryOut(**asdict(e)) for e in book.recent(level, limit, contains)]
    usage = ApiUsageOut(**asdict(services.client.api_usage()))
    return LogsResponse(items=items, capacity=book.capacity, api=usage)
