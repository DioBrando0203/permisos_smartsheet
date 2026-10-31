"""Trazo (PEN-32): de la línea dibujada a la tabla Work Location de OSP, sin abrir OSP.

Consultas: la capa 8 por trozos del trazo (vías candidatas con medida M); luego, sólo para las
vías que sigue el trazo, estatales, de condado, nombres locales y condados por atributo; y el
Turnpike en el punto medio de cada fila.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.models.map import MapTrace, SourceStatus, WorkLocation
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import (
    COUNTIES,
    COUNTY_ROADS,
    LOCAL_NAMES,
    LRS,
    STATE_ROADS,
    TURNPIKE,
    TURNPIKE_DISTRICTS,
    Layer,
    boundary_layer,
    road_layer,
)
from app.services.gis.timing import run_source
from app.services.map_mappers import feature_text, local_name_at, route_geometry, section_number
from app.services.map_rules import (
    RouteGeometry,
    in_florida,
    normalize_route,
    point_at_milepost,
    slice_route,
)
from app.services.trace_rules import Point, Run, densify, envelopes, parse_path, path_meters, runs

METERS_PER_MILE = 1609.344
Features = list[dict[str, Any]]
ByRoadway = dict[str, Features]


@dataclass(frozen=True)
class _Lookups:
    states: ByRoadway
    county_roads: ByRoadway
    names: ByRoadway
    counties: dict[str, str]


class MapTraceService:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache

    async def trace(self, text: str, radius_m: float, *, refresh: bool) -> MapTrace:
        path = self._valid_path(text)
        points = ";".join(f"{lat:.6f},{lon:.6f}" for lat, lon in path)
        return await self._cache.get_or_load(
            f"map:trace:{radius_m:.1f}:{points}",
            lambda: self._load(path, radius_m),
            refresh=refresh,
        )

    def _valid_path(self, text: str) -> list[Point]:
        path = parse_path(text)
        limit = self._settings.gis_trace_max_points
        if path is None or not 2 <= len(path) <= limit:
            message = f"El trazo necesita de 2 a {limit} puntos `lat,lon;lat,lon`."
            raise AppError("TRACE_INVALID", message, 422)
        if not all(in_florida(lat, lon) for lat, lon in path):
            raise AppError("COORDINATES_OUT_OF_FLORIDA", "El trazo sale de Florida.", 422)
        if path_meters(path) / METERS_PER_MILE > self._settings.gis_max_segment_miles:
            raise AppError("SEGMENT_TOO_LONG", "El trazo supera la longitud máxima permitida.", 422)
        return path

    async def _load(self, path: list[Point], radius_m: float) -> MapTrace:
        (routes, attrs), lrs = await self._routes(path, radius_m)
        if lrs.status != "ok" and not routes:
            raise AppError("GIS_UNAVAILABLE", "Los servicios GIS no responden.", 502)
        found = runs(densify(path), routes, radius_m)
        lookups, statuses = await self._lookups(found, attrs)
        middles = [_middle(run, routes[run.roadway_id]) for run in found]
        turnpike = await asyncio.gather(
            *(run_source("fdot_turnpike", lambda p=p: self._on_turnpike(p), None) for p in middles)
        )
        rows = [
            _row(run, routes[run.roadway_id], attrs[run.roadway_id], lookups, flag)
            for run, (flag, _) in zip(found, turnpike, strict=True)
        ]
        sources = [lrs, *statuses, *_worst([status for _, status in turnpike])]
        return MapTrace(
            path=[[round(lat, 6), round(lon, 6)] for lat, lon in path],
            length_mi=round(path_meters(path) / METERS_PER_MILE, 3),
            rows=rows,
            sources=sources,
            warnings=_warnings(rows, sources),
        )

    async def _routes(
        self, path: list[Point], radius_m: float
    ) -> tuple[tuple[dict[str, RouteGeometry], dict[str, dict[str, str]]], SourceStatus]:
        url, fields = road_layer(self._settings, LRS), ("ROADWAY", "COUNTY", "SECTION")

        async def load() -> Features:
            boxes = envelopes(path, radius_m)
            chunks = await asyncio.gather(
                *(self._client.query_box(url, box, fields, with_m=True) for box in boxes)
            )
            return [feature for features, _ in chunks for feature in features]

        features, status = await run_source("fdot_lrs", load, [])
        return _merge_routes(features), status

    async def _lookups(
        self, found: list[Run], attrs: dict[str, dict[str, str]]
    ) -> tuple[_Lookups, list[SourceStatus]]:
        # Los ID vienen del FDOT; aun así sólo dígitos entran en un filtro `where`.
        ids = sorted({run.roadway_id for run in found if run.roadway_id.isdigit()})
        codes = sorted({attrs[r]["county"] for r in ids if attrs[r]["county"].isdigit()})
        name_fields = ("ROADWAY", "NAME", "BEGIN_POST", "END_POST")
        results = await asyncio.gather(
            run_source("fdot_state_roads", lambda: self._by_roadway(STATE_ROADS, ids), {}),
            run_source("fdot_county_roads", lambda: self._by_roadway(COUNTY_ROADS, ids), {}),
            run_source(
                "fdot_local_names", lambda: self._by_roadway(LOCAL_NAMES, ids, name_fields), {}
            ),
            run_source("fdot_counties", lambda: self._county_names(codes), {}),
        )
        (states, _), (county_roads, _), (names, _), (counties, _) = results
        lookups = _Lookups(states, county_roads, names, counties)
        return lookups, [status for _, status in results] if found else []

    async def _by_roadway(
        self, layer: int, ids: list[str], fields: tuple[str, ...] = ("ROADWAY", "ROUTE")
    ) -> ByRoadway:
        if not ids:
            return {}
        where = "ROADWAY IN ({})".format(",".join(f"'{roadway}'" for roadway in ids))
        url = road_layer(self._settings, layer)
        features, _ = await self._client.query_where(url, where, fields, limit=200, geometry=False)
        grouped: ByRoadway = {}
        for feature in features:
            grouped.setdefault(feature_text(feature, "ROADWAY"), []).append(feature)
        return grouped

    async def _county_names(self, codes: list[str]) -> dict[str, str]:
        if not codes:
            return {}
        where = "CNTYNO IN ({})".format(",".join(f"'{code}'" for code in codes))
        url = boundary_layer(self._settings, COUNTIES)
        features, _ = await self._client.query_where(
            url, where, ("COUNTY", "CNTYNO"), limit=70, geometry=False
        )
        return {feature_text(f, "CNTYNO"): feature_text(f, "COUNTY") for f in features}

    async def _on_turnpike(self, point: tuple[float, float] | None) -> bool | None:
        if point is None:
            return None
        url = boundary_layer(self._settings, TURNPIKE_DISTRICTS)
        layer = Layer("fdot_turnpike", url, ("DVALUE",))
        features, _ = await self._client.query_point(layer, point[0], point[1], 0)
        return any(feature_text(feature, "DVALUE") == TURNPIKE for feature in features)


def _merge_routes(
    features: Features,
) -> tuple[dict[str, RouteGeometry], dict[str, dict[str, str]]]:
    """Una vía puede llegar en varios trozos y repetida entre rectángulos: se unen sin repetir."""
    paths: dict[str, list] = {}
    attrs: dict[str, dict[str, str]] = {}
    for feature in features:
        roadway = feature_text(feature, "ROADWAY")
        geometry = route_geometry(feature, roadway) if roadway else None
        if geometry is None:
            continue
        known = paths.setdefault(roadway, [])
        known += [path for path in geometry.paths if path not in known]
        attrs.setdefault(
            roadway,
            {
                "county": feature_text(feature, "COUNTY"),
                "section": feature_text(feature, "SECTION"),
            },
        )
    return {roadway: RouteGeometry(roadway, tuple(p)) for roadway, p in paths.items()}, attrs


def _middle(run: Run, route: RouteGeometry) -> tuple[float, float] | None:
    return point_at_milepost(route, (run.begin_milepost + run.end_milepost) / 2)


def _row(
    run: Run,
    route: RouteGeometry,
    attrs: dict[str, str],
    lookups: _Lookups,
    on_turnpike: bool | None,
) -> WorkLocation:
    roadway = run.roadway_id
    state, county = lookups.states.get(roadway), lookups.county_roads.get(roadway)
    kind = "state" if state else "county" if county else "other"
    listed = state or county
    route_name = normalize_route(feature_text(listed[0], "ROUTE")) if listed else None
    middle = (run.begin_milepost + run.end_milepost) / 2
    coordinates = slice_route(route, run.begin_milepost, run.end_milepost)
    return WorkLocation(
        county=lookups.counties.get(attrs["county"]) or None,
        state_road_id=route_name or roadway,
        roadway_id=roadway,
        section_number=section_number(attrs["section"]),
        beginning_milepost=run.begin_milepost,
        ending_milepost=run.end_milepost,
        on_turnpike=on_turnpike,
        kind=kind,
        local_name=local_name_at(lookups.names.get(roadway, []), middle),
        length_mi=round(run.length_m / METERS_PER_MILE, 3),
        geometry={"type": "LineString", "coordinates": coordinates},
    )


def _worst(statuses: list[SourceStatus]) -> list[SourceStatus]:
    """Una sola línea para el Turnpike: la primera consulta que falló, o la más lenta."""
    if not statuses:
        return []
    failed = [status for status in statuses if status.status != "ok"]
    return [failed[0] if failed else max(statuses, key=lambda status: status.ms)]


def _warnings(rows: list[WorkLocation], sources: list[SourceStatus]) -> list[str]:
    result = ["SOURCE_FAILED"] if any(source.status != "ok" for source in sources) else []
    if not rows:
        result.append("NO_ROAD_NEARBY")
    if any(row.kind != "state" for row in rows):
        result.append("NOT_STATE_ROAD")
    return result
