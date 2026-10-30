"""Buscador del mapa: dirección, calle del FDOT, ruta con milepost o coordenadas."""

import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.models.map import MapSearch, SearchResult, SourceStatus
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import COUNTY_ROADS, LOCAL_NAMES, LRS, STATE_ROADS, road_layer
from app.services.gis.transport import GisFailure
from app.services.map_mappers import feature_text, route_geometry, to_number
from app.services.map_query import (
    RouteQuery,
    address_text,
    looks_like_address,
    parse_coordinates,
    parse_route_milepost,
    route_where,
    street_rank,
    street_text,
    street_where,
)
from app.services.map_rules import in_florida, normalize_route, point_at_milepost

LIMIT = 8
Loader = Callable[[], Awaitable[list[SearchResult]]]


class MapSearchService:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache

    async def search(self, text: str, *, refresh: bool) -> MapSearch:
        query = " ".join(text.split())
        return await self._cache.get_or_load(
            f"map:search:{query.upper()}", lambda: self._load(query), refresh=refresh
        )

    async def _load(self, query: str) -> MapSearch:
        if coordinates := parse_coordinates(query):
            return MapSearch(query=query, results=_coordinate_result(*coordinates), sources=[])
        loaders: dict[str, Loader] = {}
        if route := parse_route_milepost(query):
            loaders["fdot_milepost"] = lambda: self._mileposts(route)
        else:
            if looks_like_address(query):
                loaders["census_geocoder"] = lambda: self._addresses(query)
            if cleaned := street_text(query):
                loaders["fdot_streets"] = lambda: self._streets(cleaned)
        outcomes = await asyncio.gather(*(_run(source, load) for source, load in loaders.items()))
        results = [result for found, _ in outcomes for result in found]
        return MapSearch(
            query=query, results=results[:LIMIT], sources=[status for _, status in outcomes]
        )

    async def _addresses(self, query: str) -> list[SearchResult]:
        matches, _ = await self._client.geocode(address_text(query))
        results = []
        for match in matches[:5]:
            coordinates = match.get("coordinates") or {}
            lat, lon = to_number(coordinates.get("y")), to_number(coordinates.get("x"))
            if lat is None or lon is None or not in_florida(lat, lon):
                continue
            results.append(
                SearchResult(
                    kind="address",
                    label=str(match.get("matchedAddress") or query),
                    detail="Dirección según el Censo de EE. UU.",
                    lat=round(lat, 6),
                    lon=round(lon, 6),
                )
            )
        return results

    async def _streets(self, cleaned: str) -> list[SearchResult]:
        fields = ("ROADWAY", "NAME", "COUNTY", "BEGIN_POST", "END_POST")
        path = road_layer(self._settings, LOCAL_NAMES)
        where = street_where(cleaned) or ""
        features, _ = await self._client.query_where(path, where, fields, limit=LIMIT * 3)
        features.sort(key=lambda feature: street_rank(feature_text(feature, "NAME"), cleaned))
        results = []
        for feature in features[:LIMIT]:
            middle = _middle_point(feature)
            if middle is None:
                continue
            roadway = feature_text(feature, "ROADWAY")
            county = feature_text(feature, "COUNTY")
            results.append(
                SearchResult(
                    kind="street",
                    label=feature_text(feature, "NAME") or roadway,
                    detail=_join(county, f"vía {roadway}", _range(feature)),
                    lat=middle[0],
                    lon=middle[1],
                    roadway_id=roadway,
                )
            )
        return results

    async def _mileposts(self, route: RouteQuery) -> list[SearchResult]:
        names = await self._roadways(route)
        ids = [roadway for roadway in sorted(names) if roadway.isdigit()][:LIMIT]
        if not ids:
            return []
        where = "ROADWAY IN ({})".format(",".join(f"'{roadway}'" for roadway in ids))
        fields = ("ROADWAY", "COUNTY", "BEGIN_POST", "END_POST")
        path = road_layer(self._settings, LRS)
        features, _ = await self._client.query_where(path, where, fields, limit=LIMIT, with_m=True)
        results = []
        for feature in features:
            roadway = feature_text(feature, "ROADWAY")
            geometry = route_geometry(feature, roadway)
            point = point_at_milepost(geometry, route.milepost) if geometry else None
            if point is None:
                continue
            name, county = names.get(roadway, (None, None))
            results.append(
                SearchResult(
                    kind="milepost",
                    label=f"{name or roadway} · MP {route.milepost:.3f}",
                    detail=_join(county, f"vía {roadway}"),
                    lat=point[0],
                    lon=point[1],
                    roadway_id=roadway,
                    milepost=route.milepost,
                )
            )
        return results

    async def _roadways(self, route: RouteQuery) -> dict[str, tuple[str | None, str | None]]:
        """Vías de la ruta cuyo rango de milepost contiene el pedido: {ID: (ruta, condado)}."""
        if route.system == "ROADWAY":
            return {route.number: (None, None)}
        layer = STATE_ROADS if route.system == "SR" else COUNTY_ROADS
        fields = ("ROADWAY", "ROUTE", "COUNTY", "BEGIN_POST", "END_POST")
        path = road_layer(self._settings, layer)
        features, _ = await self._client.query_where(
            path, route_where(route), fields, limit=200, geometry=False
        )
        found: dict[str, tuple[str | None, str | None]] = {}
        for feature in features:
            attrs = feature.get("attributes", {})
            begin, end = to_number(attrs.get("BEGIN_POST")), to_number(attrs.get("END_POST"))
            if begin is not None and end is not None and begin <= route.milepost <= end:
                found[feature_text(feature, "ROADWAY")] = (
                    normalize_route(attrs.get("ROUTE")),
                    feature_text(feature, "COUNTY") or None,
                )
        return found


async def _run(source: str, load: Loader) -> tuple[list[SearchResult], SourceStatus]:
    started = perf_counter()
    try:
        found, status = await load(), "ok"
    except GisFailure as error:
        found, status = [], error.status
    elapsed = round((perf_counter() - started) * 1000, 1)
    return found, SourceStatus(id=source, status=status, ms=elapsed)


def _coordinate_result(lat: float, lon: float) -> list[SearchResult]:
    if not in_florida(lat, lon):
        return []
    label = f"{lat:.6f}, {lon:.6f}"
    return [SearchResult(kind="coordinates", label=label, detail="Coordenadas", lat=lat, lon=lon)]


def _middle_point(feature: dict[str, Any]) -> tuple[float, float] | None:
    points = [point for path in feature.get("geometry", {}).get("paths", []) for point in path]
    if not points:
        return None
    lon, lat = points[len(points) // 2][:2]
    return round(float(lat), 6), round(float(lon), 6)


def _range(feature: dict[str, Any]) -> str | None:
    attrs = feature.get("attributes", {})
    begin, end = to_number(attrs.get("BEGIN_POST")), to_number(attrs.get("END_POST"))
    return None if begin is None or end is None else f"MP {begin:.3f} a {end:.3f}"


def _join(*parts: str | None) -> str:
    return " · ".join(part for part in parts if part)
