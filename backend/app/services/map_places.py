"""Condados y municipios de Florida para ubicarse en el mapa (FDOT Admin_Boundaries)."""

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.models.map import Bounds, MapArea, MapCity, MapCounty
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import CITIES, COUNTIES, boundary_layer
from app.services.map_geometry import Box, Line, bounds_of, contains
from app.services.map_mappers import feature_text, to_number
from app.services.map_query import name_where

# Contornos simplificados a unos 50 m: alcanzan para dibujar y para decidir pertenencia.
SIMPLIFY_DEGREES = 0.0005
# CLASSFP del Censo: C1 es municipio; U1 y U2 son zonas no incorporadas con nombre (CDP).
INCORPORATED = "C1"


@dataclass(frozen=True)
class Place:
    name: str
    rings: list[Line]
    box: Box


@dataclass(frozen=True)
class CountyPlaces:
    county: MapCounty
    outline: Place
    cities: list[Place]


@dataclass(frozen=True)
class Scope:
    """Zona elegida para acotar el buscador: rectángulo y centro (lon, lat)."""

    county: str
    city: str | None
    box: Box
    center: tuple[float, float]


class MapPlacesService:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache

    async def counties(self) -> list[MapCounty]:
        return await self._cache.get_or_load("map:counties", self._load_counties)

    async def area(self, county: str, city: str | None) -> MapArea:
        places = await self._county(county)
        chosen = _city(places, city) if city else places.outline
        return MapArea(
            county=places.county.name,
            code_fdot=places.county.code_fdot,
            city=chosen.name if city else None,
            bounds=_bounds(chosen.box),
            outline=[[[lon, lat] for lon, lat in ring] for ring in chosen.rings],
            cities=[MapCity(name=place.name, bounds=_bounds(place.box)) for place in places.cities],
        )

    async def scope(self, county: str | None, city: str | None) -> Scope | None:
        if not county:
            return None
        places = await self._county(county)
        chosen = _city(places, city) if city else places.outline
        west, south, east, north = chosen.box
        center = ((west + east) / 2, (south + north) / 2)
        return Scope(places.county.name, chosen.name if city else None, chosen.box, center)

    async def _county(self, name: str) -> CountyPlaces:
        wanted = name.strip().upper()
        county = next((item for item in await self.counties() if item.name.upper() == wanted), None)
        if county is None:
            raise AppError("MAP_AREA_NOT_FOUND", "No se encontró ese condado de Florida.", 404)
        return await self._cache.get_or_load(
            f"map:county:{county.name}", lambda: self._load_county(county)
        )

    async def _load_counties(self) -> list[MapCounty]:
        path = boundary_layer(self._settings, COUNTIES)
        fields = ("COUNTY", "CNTYNO")
        features, _ = await self._client.query_where(path, "1=1", fields, limit=100, geometry=False)
        found = {feature_text(item, "COUNTY"): feature_text(item, "CNTYNO") for item in features}
        return [
            MapCounty(name=name, code_fdot=code) for name, code in sorted(found.items()) if name
        ]

    async def _load_county(self, county: MapCounty) -> CountyPlaces:
        path = boundary_layer(self._settings, COUNTIES)
        where = name_where("COUNTY", county.name)
        features, _ = await self._client.query_where(
            path, where, ("COUNTY",), limit=5, simplify_degrees=SIMPLIFY_DEGREES
        )
        rings = [ring for feature in features for ring in _rings(feature)]
        box = bounds_of(rings)
        if box is None:
            raise AppError(
                "MAP_AREA_NOT_FOUND", "El FDOT no devolvió el contorno del condado.", 404
            )
        fields = ("NAME", "CLASSFP", "INTPTLAT", "INTPTLON")
        cities, _ = await self._client.query_box(
            boundary_layer(self._settings, CITIES), box, fields, simplify_degrees=SIMPLIFY_DEGREES
        )
        return CountyPlaces(county, Place(county.name, rings, box), _municipalities(cities, rings))


def _municipalities(features: list[dict[str, Any]], county: list[Line]) -> list[Place]:
    """Sólo municipios cuyo punto interior cae en el condado: el rectángulo trae vecinos."""
    found: dict[str, list[Line]] = {}
    for feature in features:
        attrs = feature.get("attributes", {})
        lat, lon = to_number(attrs.get("INTPTLAT")), to_number(attrs.get("INTPTLON"))
        if attrs.get("CLASSFP") != INCORPORATED or lat is None or lon is None:
            continue
        if contains(county, lon, lat):
            found.setdefault(feature_text(feature, "NAME"), []).extend(_rings(feature))
    places = [Place(name, rings, box) for name, rings in found.items() if (box := bounds_of(rings))]
    return sorted(places, key=lambda place: place.name)


def _city(places: CountyPlaces, name: str) -> Place:
    wanted = name.strip().upper()
    match = next((place for place in places.cities if place.name.upper() == wanted), None)
    if match is None:
        raise AppError("MAP_AREA_NOT_FOUND", "Esa ciudad no está en el condado elegido.", 404)
    return match


def _rings(feature: dict[str, Any]) -> list[Line]:
    rings = feature.get("geometry", {}).get("rings", [])
    return [[(float(point[0]), float(point[1])) for point in ring] for ring in rings]


def _bounds(box: Box) -> Bounds:
    west, south, east, north = (round(value, 6) for value in box)
    return Bounds(west=west, south=south, east=east, north=north)
