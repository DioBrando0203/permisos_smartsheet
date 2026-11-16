"""Calles del condado con quién las mantiene, por celda y a lo largo de un trazo (PEN-41).

La fuente se elige por el rectángulo de cada adaptador (SPEC-B14 puntos 14 y 15): no hace falta
preguntar al FDOT de qué condado es el centro, y una celda fuera de todo adaptador no consulta.
"""

import asyncio
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.models.map import StreetLines, TraceStreets
from app.services.cache import TtlCache
from app.services.county_roads import Box, CountyAdapter, adapter_for_box
from app.services.gis import GisClient
from app.services.gis.timing import run_source
from app.services.gis.transport import GisFailure
from app.services.map_rules import in_florida
from app.services.map_trace import valid_trace_path
from app.services.trace_rules import Point, envelopes, path_meters
from app.services.trace_streets import METERS_PER_MILE, group_streets, street_line, street_rows

CELL_MAX_DEGREES = 0.02
# ~1 m: no se nota a zoom 18 y baja el peso de los tramos curvos.
SIMPLIFY_DEGREES = 0.00001
LIMIT = 1000
FIELDS = ("OBJECTID", "NAME", "MAINTENANCE", "GATED")


class CountyStreetsService:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache

    async def lines(self, box: Box, *, refresh: bool) -> StreetLines:
        west, south, east, north = box
        limit = CELL_MAX_DEGREES + 1e-9  # -81.46 - -81.48 da 0.0200000000000102
        if not (0 < east - west <= limit and 0 < north - south <= limit):
            message = f"La celda debe medir como máximo {CELL_MAX_DEGREES} grados por lado."
            raise AppError("STREET_CELL_INVALID", message, 422)
        if not in_florida((south + north) / 2, (west + east) / 2):
            raise AppError("COORDINATES_OUT_OF_FLORIDA", "La celda está fuera de Florida.", 422)
        adapter = adapter_for_box(self._settings, box)
        if adapter is None:
            return StreetLines(streets=[])
        key = "map:streets:" + ":".join(f"{value:.5f}" for value in box)
        return await self._cache.get_or_load(
            key, lambda: self._lines(adapter, box), refresh=refresh
        )

    async def trace(self, text: str, radius_m: float, *, refresh: bool) -> TraceStreets:
        path = valid_trace_path(text, self._settings)
        lats, lons = [point[0] for point in path], [point[1] for point in path]
        adapter = adapter_for_box(self._settings, (min(lons), min(lats), max(lons), max(lats)))
        if adapter is None:
            unmatched = round(path_meters(path) / METERS_PER_MILE, 3)
            return TraceStreets(
                streets=[], unmatched_length_mi=unmatched, sources=[], warnings=["NO_COUNTY_SOURCE"]
            )
        points = ";".join(f"{lat:.6f},{lon:.6f}" for lat, lon in path)
        return await self._cache.get_or_load(
            f"map:trace-streets:{radius_m:.1f}:{points}",
            lambda: self._trace(adapter, path, radius_m),
            refresh=refresh,
        )

    async def _lines(self, adapter: CountyAdapter, box: Box) -> StreetLines:
        try:
            features, _ = await self._client.query_box(
                adapter.layer.path, box, FIELDS, simplify_degrees=SIMPLIFY_DEGREES, limit=LIMIT
            )
        except GisFailure:
            message = "La fuente de calles del condado no responde."
            raise AppError("GIS_UNAVAILABLE", message, 502) from None
        streets = [line for feature in features if (line := street_line(adapter, feature))]
        return StreetLines(
            source=adapter.layer.id,
            county=adapter.county,
            streets=streets,
            truncated=len(features) >= LIMIT,
        )

    async def _trace(
        self, adapter: CountyAdapter, path: list[Point], radius_m: float
    ) -> TraceStreets:
        boxes = envelopes(path, radius_m)

        async def load() -> list[list[dict[str, Any]]]:
            chunks = await asyncio.gather(
                *(
                    self._client.query_box(adapter.layer.path, box, FIELDS, limit=LIMIT)
                    for box in boxes
                )
            )
            return [features for features, _ in chunks]

        chunks, status = await run_source(adapter.layer.id, load, [])
        if status.status != "ok":
            message = "La fuente de calles del condado no responde."
            raise AppError("GIS_UNAVAILABLE", message, 502)
        features = [feature for chunk in chunks for feature in chunk]
        rows, unmatched = street_rows(adapter, group_streets(features), path, radius_m)
        warnings = ["TRACE_PARTIAL"] if unmatched >= 1 else []
        if any(len(chunk) >= LIMIT for chunk in chunks):
            warnings.append("STREETS_TRUNCATED")
        return TraceStreets(
            county=adapter.county,
            source=adapter.layer.id,
            streets=rows,
            unmatched_length_mi=round(unmatched / METERS_PER_MILE, 3),
            sources=[status],
            warnings=warnings,
        )
