"""Buscador del mapa: dirección, calle, cruce de calles, ruta con milepost o coordenadas.

Con un condado (y una ciudad) elegidos, cada fuente se acota a esa zona y se suman las calles
locales del Censo; sin zona se busca en todo Florida sólo en las vías del FDOT.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import Settings
from app.models.map import MapSearch, SearchResult
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import COUNTY_ROADS, LOCAL_NAMES, LRS, STATE_ROADS, road_layer
from app.services.gis.timing import run_source
from app.services.map_mappers import feature_text, route_geometry, to_number
from app.services.map_places import MapPlacesService, Scope
from app.services.map_query import (
    RouteQuery,
    address_text,
    join_parts,
    looks_like_address,
    name_where,
    parse_coordinates,
    parse_intersection,
    parse_route_milepost,
    route_where,
    street_rank,
    street_text,
    street_where,
)
from app.services.map_rules import haversine_miles, in_florida, normalize_route, point_at_milepost
from app.services.map_streets import StreetFinder

LIMIT = 8
# Resultados de fuentes distintas a menos de esto (unos 30 m) son el mismo lugar.
SAME_PLACE_MILES = 0.02
Loader = Callable[[], Awaitable[list[SearchResult]]]


class MapSearchService:
    def __init__(
        self, settings: Settings, client: GisClient, cache: TtlCache, places: MapPlacesService
    ) -> None:
        self._settings, self._client, self._cache = settings, client, cache
        self._places = places
        self._streets_finder = StreetFinder(settings, client, cache)

    async def search(
        self, text: str, *, county: str | None = None, city: str | None = None, refresh: bool
    ) -> MapSearch:
        query = " ".join(text.split())
        scope = await self._places.scope(county, city)
        where = f"{scope.county}/{scope.city or ''}" if scope else ""
        return await self._cache.get_or_load(
            f"map:search:{where}:{query.upper()}", lambda: self._load(query, scope), refresh=refresh
        )

    async def _load(self, query: str, scope: Scope | None) -> MapSearch:
        if coordinates := parse_coordinates(query):
            return MapSearch(query=query, results=_coordinate_result(*coordinates), sources=[])
        outcomes = await asyncio.gather(
            *(run_source(source, load, []) for source, load in self._loaders(query, scope).items())
        )
        results = _distinct([result for found, _ in outcomes for result in found])
        return MapSearch(
            query=query, results=results[:LIMIT], sources=[status for _, status in outcomes]
        )

    def _loaders(self, query: str, scope: Scope | None) -> dict[str, Loader]:
        finder, county = self._streets_finder, scope.county if scope else None
        if route := parse_route_milepost(query):
            return {"fdot_milepost": lambda: self._mileposts(route, county)}
        if crossing := parse_intersection(query):
            first, second = crossing
            loaders: dict[str, Loader] = {
                "fdot_crossings": lambda: finder.fdot_crossings(first, second, county),
                "census_geocoder": lambda: finder.census_crossing(first, second, scope),
            }
            if scope:
                loaders["tiger_crossings"] = lambda: finder.tiger_crossing(first, second, scope)
            return loaders
        loaders = {}
        if looks_like_address(query):
            loaders["census_geocoder"] = lambda: self._addresses(query, scope)
        if cleaned := street_text(query):
            loaders["fdot_streets"] = lambda: self._streets(cleaned, county)
            if scope:
                loaders["tiger_streets"] = lambda: finder.tiger_streets(query, scope)
        return loaders

    async def _addresses(self, query: str, scope: Scope | None) -> list[SearchResult]:
        matches, _ = await self._client.geocode(address_text(query, scope.city if scope else None))
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

    async def _streets(self, cleaned: str, county: str | None) -> list[SearchResult]:
        fields = ("ROADWAY", "NAME", "COUNTY", "BEGIN_POST", "END_POST")
        path = road_layer(self._settings, LOCAL_NAMES)
        where = street_where(cleaned) or ""
        if county:
            where = f"{where} AND {name_where('COUNTY', county)}"
        features, _ = await self._client.query_where(path, where, fields, limit=LIMIT * 3)
        features.sort(key=lambda feature: street_rank(feature_text(feature, "NAME"), cleaned))
        results = []
        for feature in features[:LIMIT]:
            middle = _middle_point(feature)
            if middle is None:
                continue
            roadway = feature_text(feature, "ROADWAY")
            county_name = feature_text(feature, "COUNTY")
            results.append(
                SearchResult(
                    kind="street",
                    label=feature_text(feature, "NAME") or roadway,
                    detail=join_parts(county_name, f"vía {roadway}", _range(feature)),
                    lat=middle[0],
                    lon=middle[1],
                    roadway_id=roadway,
                )
            )
        return results

    async def _mileposts(self, route: RouteQuery, county: str | None) -> list[SearchResult]:
        names = await self._roadways(route)
        if county:
            names = {key: value for key, value in names.items() if value[1] == county}
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
            name, county_name = names.get(roadway, (None, None))
            results.append(
                SearchResult(
                    kind="milepost",
                    label=f"{name or roadway} · MP {route.milepost:.3f}",
                    detail=join_parts(county_name, f"vía {roadway}"),
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


def _distinct(results: list[SearchResult]) -> list[SearchResult]:
    """Junta el mismo lugar visto por varias fuentes; gana el primero (FDOT trae milepost)."""
    kept: list[SearchResult] = []
    for result in results:
        if not any(
            other.kind == result.kind
            and haversine_miles(other.lat, other.lon, result.lat, result.lon) < SAME_PLACE_MILES
            for other in kept
        ):
            kept.append(result)
    return kept


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
