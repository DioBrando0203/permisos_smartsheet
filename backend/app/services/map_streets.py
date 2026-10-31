"""Calles y cruces de calles: TIGER del Censo en la zona elegida, cruces del FDOT y Censo."""

import asyncio

from app.core.config import Settings
from app.models.map import SearchResult
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import INTERSECTIONS, LOCAL_NAMES, TIGER_ROADS, road_layer, tiger_layer
from app.services.map_geometry import Line, closest_points, nearest_vertex
from app.services.map_mappers import feature_text, to_number
from app.services.map_places import Scope
from app.services.map_query import (
    address_text,
    join_parts,
    name_where,
    street_rank,
    street_text,
    street_where,
    tiger_where,
)
from app.services.map_rules import in_florida

LIMIT = 8
# Dos calles a menos de esto se consideran cruzadas: los ejes TIGER no siempre se tocan.
CROSSING_METERS = 15.0
# Variantes de nombre por calle que se comparan entre sí ("E Las Olas Blvd", "W Las Olas Blvd").
NAMES_PER_STREET = 6


class StreetFinder:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache

    async def tiger_streets(self, text: str, scope: Scope) -> list[SearchResult]:
        """Todas las calles (también locales) de la zona, una por nombre, en su punto central."""
        lines = await self._tiger_lines(text, scope)
        place = scope.city or scope.county
        results = []
        for name in _ranked(lines, text)[:LIMIT]:
            vertex = nearest_vertex(lines[name], *scope.center)
            if vertex:
                lat, lon = round(vertex[1], 6), round(vertex[0], 6)
                detail = join_parts(place, "Calle según el Censo de EE. UU.")
                results.append(
                    SearchResult(kind="street", label=name, detail=detail, lat=lat, lon=lon)
                )
        return results

    async def tiger_crossing(self, first: str, second: str, scope: Scope) -> list[SearchResult]:
        """Cruces exactos entre las dos calles; si no se cruzan, el punto más cercano."""
        lines_a, lines_b = await asyncio.gather(
            self._tiger_lines(first, scope), self._tiger_lines(second, scope)
        )
        pairs = []
        for name_a in _ranked(lines_a, first)[:NAMES_PER_STREET]:
            for name_b in _ranked(lines_b, second)[:NAMES_PER_STREET]:
                found = (
                    closest_points(lines_a[name_a], lines_b[name_b]) if name_a != name_b else None
                )
                if found:
                    pairs.append((found[2], name_a, name_b, found))
        pairs.sort()
        crossings = [pair for pair in pairs if pair[0] <= CROSSING_METERS]
        return [_crossing_result(*pair[1:], scope) for pair in (crossings or pairs[:1])][:LIMIT]

    async def fdot_crossings(
        self, first: str, second: str, county: str | None
    ) -> list[SearchResult]:
        """Cruces sobre vías del FDOT, con el milepost exacto del cruce (RCI, capa 6)."""
        found = await asyncio.gather(
            self._fdot_crossings(first, second, county),
            self._fdot_crossings(second, first, county),
        )
        return [result for results in found for result in results]

    async def census_crossing(
        self, first: str, second: str, scope: Scope | None
    ) -> list[SearchResult]:
        city = scope.city if scope else None
        matches, _ = await self._client.geocode(address_text(f"{first} & {second}", city))
        results = []
        for match in matches[:3]:
            coordinates = match.get("coordinates") or {}
            lat, lon = to_number(coordinates.get("y")), to_number(coordinates.get("x"))
            if lat is not None and lon is not None and in_florida(lat, lon):
                label = str(match.get("matchedAddress") or f"{first} & {second}")
                detail = "Cruce según el Censo de EE. UU."
                lat, lon = round(lat, 6), round(lon, 6)
                results.append(
                    SearchResult(kind="intersection", label=label, detail=detail, lat=lat, lon=lon)
                )
        return results

    async def _fdot_crossings(
        self, road: str, crossing: str, county: str | None
    ) -> list[SearchResult]:
        names = await self._fdot_roads(road, county)
        crossing_where = street_where(crossing, "INTSEC_ROA")
        ids = [roadway for roadway in sorted(names) if roadway.isdigit()][:20]
        if not ids or not crossing_where:
            return []
        roadways = ",".join(f"'{roadway}'" for roadway in ids)
        where = f"ROADWAY IN ({roadways}) AND {crossing_where}"
        fields = ("ROADWAY", "INTSEC_ROA", "BEGIN_POST", "COUNTY")
        path = road_layer(self._settings, INTERSECTIONS)
        features, _ = await self._client.query_where(path, where, fields, limit=LIMIT * 2)
        results: dict[tuple[str, float], SearchResult] = {}
        for feature in features:
            roadway, geometry = feature_text(feature, "ROADWAY"), feature.get("geometry", {})
            milepost = to_number(feature.get("attributes", {}).get("BEGIN_POST"))
            lat, lon = to_number(geometry.get("y")), to_number(geometry.get("x"))
            if milepost is None or lat is None or lon is None or (roadway, milepost) in results:
                continue
            results[(roadway, milepost)] = SearchResult(
                kind="intersection",
                label=f"{names[roadway]} y {feature_text(feature, 'INTSEC_ROA')}",
                detail=join_parts(feature_text(feature, "COUNTY"), f"vía {roadway}"),
                lat=round(lat, 6),
                lon=round(lon, 6),
                roadway_id=roadway,
                milepost=round(milepost, 3),
            )
        return list(results.values())

    async def _fdot_roads(self, text: str, county: str | None) -> dict[str, str]:
        where = street_where(text)
        if not where:
            return {}
        if county:
            where = f"{where} AND {name_where('COUNTY', county)}"
        path = road_layer(self._settings, LOCAL_NAMES)
        features, _ = await self._client.query_where(
            path, where, ("ROADWAY", "NAME"), limit=50, geometry=False
        )
        return {feature_text(item, "ROADWAY"): feature_text(item, "NAME") for item in features}

    async def _tiger_lines(self, text: str, scope: Scope) -> dict[str, list[Line]]:
        """Calles TIGER por nombre en la zona, en caché: al seguir escribiendo no se repiten.

        El firewall del Censo bloquea la IP si recibe muchas consultas seguidas (2026-10-31).
        """
        where = tiger_where(text)
        if not where:
            return {}
        key = f"map:tiger:{scope.box}:{where}"
        return await self._cache.get_or_load(key, lambda: self._load_tiger(where, scope))

    async def _load_tiger(self, where: str, scope: Scope) -> dict[str, list[Line]]:
        responses = await asyncio.gather(
            *(
                self._client.query_where(
                    tiger_layer(self._settings, layer), where, ("NAME",), limit=500, box=scope.box
                )
                for layer in TIGER_ROADS
            )
        )
        grouped: dict[str, list[Line]] = {}
        for features, _ in responses:
            for feature in features:
                paths = feature.get("geometry", {}).get("paths", [])
                lines = [[(float(point[0]), float(point[1])) for point in path] for path in paths]
                grouped.setdefault(feature_text(feature, "NAME"), []).extend(lines)
        grouped.pop("", None)
        return grouped


def _ranked(lines: dict[str, list[Line]], text: str) -> list[str]:
    cleaned = street_text(text) or ""
    return sorted(lines, key=lambda name: street_rank(name.upper(), cleaned))


def _crossing_result(
    name_a: str, name_b: str, found: tuple[float, float, float], scope: Scope
) -> SearchResult:
    lat, lon, meters = found
    place = scope.city or scope.county
    if meters <= CROSSING_METERS:
        detail = join_parts(place, "Cruce calculado con calles del Censo")
        label = f"{name_a} y {name_b}"
        return SearchResult(kind="intersection", label=label, detail=detail, lat=lat, lon=lon)
    detail = join_parts(place, f"No se cruzan: punto más cercano a {meters:.0f} m")
    return SearchResult(
        kind="nearest",
        label=f"{name_a} y {name_b}",
        detail=detail,
        lat=lat,
        lon=lon,
        distance_m=meters,
    )
