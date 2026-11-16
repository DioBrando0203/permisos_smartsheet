"""Calles del condado que sigue un trazo (PEN-41, SPEC-B14 punto 15). Puro.

Misma regla que las filas de Work Location (punto 10): muestras cada 10 m, cada una en la calle
más cercana dentro del radio sin cambiar mientras la actual siga en el radio, y filas de menos de
20 m descartadas. Una calle es el conjunto de tramos con el mismo nombre y responsable.
"""

import math
from dataclasses import dataclass
from typing import Any

from app.models.map import StreetLine, TraceStreet
from app.services.county_roads import OUT_OF_COUNTY, Box, CountyAdapter
from app.services.map_mappers import feature_text, route_geometry
from app.services.map_rules import RouteGeometry, distance_m_to_route
from app.services.trace_rules import Point, densify, kept_groups, meters_between, path_meters

METERS_PER_MILE = 1609.344


@dataclass(frozen=True)
class Street:
    name: str | None
    maintainer: str
    gated: bool
    segments: tuple[RouteGeometry, ...]
    route: RouteGeometry
    box: Box


def street_line(adapter: CountyAdapter, feature: dict[str, Any]) -> StreetLine | None:
    """Tramo para dibujar (punto 14); None si está fuera del condado o no tiene geometría."""
    maintainer = feature_text(feature, "MAINTENANCE")
    paths = _paths(feature)
    if maintainer == OUT_OF_COUNTY or not paths:
        return None
    authority, name = adapter.classify(maintainer)
    return StreetLine(
        id=feature_text(feature, "OBJECTID"),
        name=feature_text(feature, "NAME") or None,
        maintainer=maintainer,
        authority=authority,
        authority_name=name,
        gated=feature_text(feature, "GATED") == "Y",
        paths=paths,
    )


def group_streets(features: list[dict[str, Any]]) -> dict[str, Street]:
    """Tramos con el mismo nombre y responsable forman una calle; sin repetir `OBJECTID`."""
    seen: set[str] = set()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for feature in features:
        oid = feature_text(feature, "OBJECTID")
        if oid in seen or feature_text(feature, "MAINTENANCE") == OUT_OF_COUNTY:
            continue
        seen.add(oid)
        key = f"{feature_text(feature, 'NAME')}|{feature_text(feature, 'MAINTENANCE')}"
        grouped.setdefault(key, []).append(feature)
    return {key: street for key, items in grouped.items() if (street := _street(items))}


def street_rows(
    adapter: CountyAdapter, streets: dict[str, Street], path: list[Point], radius_m: float
) -> tuple[list[TraceStreet], float]:
    """Una fila por calle que sigue el trazo, en orden, y los metros sin calle del condado."""
    samples = densify(path)
    near = [_near(point, streets, radius_m) for point in samples]
    runs: list[tuple[str, list[list[Point]]]] = []
    for key, first, last in kept_groups(samples, near):
        # La misma calle seguida, con un hueco en medio, es una fila: el hueco va en `unmatched`.
        if runs and runs[-1][0] == key:
            runs[-1][1].append(samples[first : last + 1])
        else:
            runs.append((key, [samples[first : last + 1]]))
    rows = [_row(adapter, streets[key], pieces, radius_m) for key, pieces in runs]
    unmatched = sum(
        meters_between(first, last)
        for index, (first, last) in enumerate(zip(samples, samples[1:], strict=False))
        if not (near[index] and near[index + 1])
    )
    return rows, unmatched


def _row(
    adapter: CountyAdapter, street: Street, pieces: list[list[Point]], radius_m: float
) -> TraceStreet:
    authority, name = adapter.classify(street.maintainer)
    samples = [point for piece in pieces for point in piece]
    touched = [
        segment
        for segment in street.segments
        if any(_within(point, segment, radius_m) for point in samples)
    ]
    return TraceStreet(
        name=street.name,
        maintainer=street.maintainer,
        authority=authority,
        authority_name=name,
        gated=street.gated,
        length_mi=round(sum(path_meters(piece) for piece in pieces) / METERS_PER_MILE, 3),
        paths=[_lon_lat(path) for segment in touched for path in segment.paths],
    )


def _near(point: Point, streets: dict[str, Street], radius_m: float) -> dict[str, float]:
    pad_lat = radius_m / 111_320
    pad_lon = pad_lat / math.cos(math.radians(point[0]))
    found = {}
    for key, street in streets.items():
        west, south, east, north = street.box
        if not (west - pad_lon <= point[1] <= east + pad_lon):
            continue
        if not (south - pad_lat <= point[0] <= north + pad_lat):
            continue
        distance = distance_m_to_route(point[0], point[1], street.route)
        if distance is not None and distance <= radius_m:
            found[key] = distance
    return found


def _within(point: Point, segment: RouteGeometry, radius_m: float) -> bool:
    distance = distance_m_to_route(point[0], point[1], segment)
    return distance is not None and distance <= radius_m


def _street(features: list[dict[str, Any]]) -> Street | None:
    segments = tuple(
        route for feature in features if (route := route_geometry(feature, "")) is not None
    )
    if not segments:
        return None
    paths = tuple(path for segment in segments for path in segment.paths)
    lons = [vertex[0] for path in paths for vertex in path]
    lats = [vertex[1] for path in paths for vertex in path]
    first = features[0]
    return Street(
        name=feature_text(first, "NAME") or None,
        maintainer=feature_text(first, "MAINTENANCE"),
        gated=any(feature_text(feature, "GATED") == "Y" for feature in features),
        segments=segments,
        route=RouteGeometry("", paths),
        box=(min(lons), min(lats), max(lons), max(lats)),
    )


def _paths(feature: dict[str, Any]) -> list[list[list[float]]]:
    route = route_geometry(feature, "")
    return [_lon_lat(path) for path in route.paths if len(path) > 1] if route else []


def _lon_lat(path: tuple[tuple[float, float, float | None], ...]) -> list[list[float]]:
    return [[round(vertex[0], 6), round(vertex[1], 6)] for vertex in path]
