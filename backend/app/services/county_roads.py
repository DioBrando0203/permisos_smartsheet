"""Adaptadores de condado (M5): de quién es la calle según el eje de calles del condado.

Puro salvo la elección de capa. St. Johns (PEN-40, MJ-SJ-03): `MAINTENANCE` dice quién
mantiene cada tramo; reemplaza la aproximación por ciudad o zona no incorporada.
"""

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.models.map import Jurisdiction, MapLocation, RoadMatch, StreetAuthority
from app.services.gis.layers import ST_JOHNS_FDOT, Layer, stjohns_roads
from app.services.map_mappers import feature_text, route_geometry
from app.services.map_rules import distance_m_to_route, jurisdiction

Authority = StreetAuthority
Box = tuple[float, float, float, float]  # (oeste, sur, este, norte)
# Extensión del condado 78 en el FDOT (-81.692, 29.622, -81.213, 30.253) con margen (PEN-41).
ST_JOHNS_BOUNDS: Box = (-81.70, 29.61, -81.20, 30.26)
# Tramos fuera del condado: la capa los trae en los bordes, pero no son de St. Johns.
OUT_OF_COUNTY = "Out of County"

# Valores de `MAINTENANCE` con dueño conocido. `Proposed`, `Emergency Access`,
# `Out of County` y vacío no dicen quién mantiene la calle y no cuentan.
ST_JOHNS_MAINTAINERS: dict[str, tuple[Authority, str]] = {
    "St Johns County": ("COUNTY", "St. Johns County"),
    "Parks and Recreation": ("COUNTY", "St. Johns County (Parques y Recreación)"),
    "City of St Augustine": ("CITY", "City of St. Augustine"),
    "City of St Augustine Beach": ("CITY", "City of St. Augustine Beach"),
    "State of Florida": ("FDOT", "FDOT"),
    "Private": ("PRIVATE", "Privada"),
    "Private CDD": ("SPECIAL_DISTRICT", "CDD (Community Development District)"),
}


@dataclass(frozen=True)
class CountyAdapter:
    layer: Layer
    county: str
    maintainers: dict[str, tuple[Authority, str]]
    bounds: Box = ST_JOHNS_BOUNDS

    def classify(self, maintainer: str) -> tuple[Authority, str] | tuple[None, None]:
        """Autoridad y nombre del valor del condado; (None, None) si no dice quién la mantiene."""
        return self.maintainers.get(maintainer) or (None, None)


@dataclass(frozen=True)
class CountyStreet:
    county: str
    name: str | None
    maintainer: str
    authority: Authority
    authority_name: str
    distance_m: float
    gated: bool


def county_adapter(settings: Settings, county_fdot: str | None) -> CountyAdapter | None:
    """Adaptador del condado del punto (código FDOT), o None si no tiene fuente propia."""
    if county_fdot == ST_JOHNS_FDOT:
        return CountyAdapter(stjohns_roads(settings), "St. Johns", ST_JOHNS_MAINTAINERS)
    return None


def adapter_for_box(settings: Settings, box: Box) -> CountyAdapter | None:
    """Adaptador cuyo rectángulo toca el pedido; sin consultar el condado del centro."""
    adapter = county_adapter(settings, ST_JOHNS_FDOT)
    if adapter and _overlaps(adapter.bounds, box):
        return adapter
    return None


def _overlaps(first: Box, second: Box) -> bool:
    return (
        first[0] <= second[2]
        and second[0] <= first[2]
        and first[1] <= second[3]
        and second[1] <= first[3]
    )


def nearest_street(
    adapter: CountyAdapter, features: list[dict[str, Any]], lat: float, lon: float
) -> CountyStreet | None:
    """Tramo más cercano al punto entre los que tienen dueño conocido."""
    streets = [street for feature in features if (street := _street(adapter, feature, lat, lon))]
    return min(streets, key=lambda street: street.distance_m, default=None)


def street_jurisdiction(
    roads: list[RoadMatch], location: MapLocation, street: CountyStreet | None
) -> Jurisdiction:
    """Regla del punto 5 de SPEC-B14: el condado gana salvo una vía estatal del FDOT más cerca."""
    nearest = roads[0] if roads else None
    base = jurisdiction(nearest, location)
    if street is None:
        return base
    said = _said(street)
    if (
        nearest is not None
        and nearest.kind == "state"
        and street.authority != "FDOT"
        and nearest.distance_m <= street.distance_m
    ):
        return base.model_copy(update={"note": f"{base.note} {said}"})
    confirmed = street.authority != "FDOT" or any(road.kind == "state" for road in roads)
    return Jurisdiction(
        authority=street.authority,
        name=street.authority_name,
        basis="county_maintenance",
        confidence="high" if confirmed else "medium",
        note=said if confirmed else f"{said} El FDOT no la tiene como vía estatal: confirmar.",
    )


def _street(
    adapter: CountyAdapter, feature: dict[str, Any], lat: float, lon: float
) -> CountyStreet | None:
    maintainer = feature_text(feature, "MAINTENANCE")
    known = adapter.maintainers.get(maintainer)
    route = route_geometry(feature, maintainer)
    distance = distance_m_to_route(lat, lon, route) if route else None
    if known is None or distance is None:
        return None
    return CountyStreet(
        county=adapter.county,
        name=feature_text(feature, "NAME") or None,
        maintainer=maintainer,
        authority=known[0],
        authority_name=known[1],
        distance_m=distance,
        gated=feature_text(feature, "GATED") == "Y",
    )


def _said(street: CountyStreet) -> str:
    name = street.name or "calle sin nombre"
    gated = " (con portón)" if street.gated else ""
    source = f"Según el condado de {street.county}"
    return f"{source}: {name}{gated}, mantenimiento «{street.maintainer}»."
