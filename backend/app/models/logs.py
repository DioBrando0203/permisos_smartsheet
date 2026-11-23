"""Contrato de `GET /api/ids/logs`: eventos del servicio y consumo de API (SPEC-B21)."""

from pydantic import BaseModel


class LogEntryOut(BaseModel):
    at: str
    level: str
    source: str
    message: str


class ApiUsageOut(BaseModel):
    last_minute: int
    last_hour: int
    total: int
    rate_limited: int
    throttled: int
    max_per_minute: int


class LogsResponse(BaseModel):
    items: list[LogEntryOut]
    capacity: int
    api: ApiUsageOut
