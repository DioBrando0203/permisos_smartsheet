"""Reglas geométricas y de jurisdicción puras para el módulo Mapa."""

import math
from dataclasses import dataclass

from app.models.map import Jurisdiction, MapLocation, RoadMatch

DOR_USES = {
    "086": ("Gobierno del condado", "county"),
    "087": ("Gobierno estatal", "state"),
    "088": ("Gobierno federal", "federal"),
    "089": ("Gobierno municipal", "municipal"),
    "094": ("Derecho de vía", "right_of_way"),
}


@dataclass(frozen=True)
class RouteGeometry:
    roadway_id: str
    paths: tuple[tuple[tuple[float, float, float | None], ...], ...]


def in_florida(lat: float, lon: float) -> bool:
    """Rectángulo de seguridad del producto: las fuentes base son sólo de Florida."""
    return 24.3 <= lat <= 31.1 and -87.7 <= lon <= -79.8


def normalize_route(value: object) -> str | None:
    """Normaliza los espacios irregulares que devuelve FDOT, como `SR  953`."""
    text = " ".join(str(value or "").split())
    return text or None


def milepost_at(lat: float, lon: float, route: RouteGeometry) -> float | None:
    """Proyecta el punto al segmento LRS más cercano e interpola su medida M."""
    best: tuple[float, float] | None = None
    for path in route.paths:
        for first, second in zip(path, path[1:], strict=False):
            if first[2] is None or second[2] is None:
                continue
            ratio, distance = _projection(lon, lat, first[0], first[1], second[0], second[1])
            milepost = first[2] + ratio * (second[2] - first[2])
            if best is None or distance < best[0]:
                best = (distance, milepost)
    return round(best[1], 3) if best else None


def distance_m_to_route(lat: float, lon: float, route: RouteGeometry) -> float | None:
    """Distancia aproximada para ordenar vías cuando ArcGIS no entrega `distance`."""
    distances = [
        _projection(lon, lat, first[0], first[1], second[0], second[1])[1]
        for path in route.paths
        for first, second in zip(path, path[1:], strict=False)
    ]
    if not distances:
        return None
    return round(math.sqrt(min(distances)) * 111_000, 1)


def slice_route(route: RouteGeometry, begin: float, end: float) -> list[list[float]]:
    """Recorta una trayectoria LRS entre medidas; conserva una línea segura si falta M."""
    low, high = sorted((begin, end))
    for path in route.paths:
        sliced = _slice_path(path, low, high)
        if len(sliced) >= 2:
            return [[round(lon, 6), round(lat, 6)] for lon, lat, _ in sliced]
    return []


def point_at_milepost(route: RouteGeometry, milepost: float) -> tuple[float, float] | None:
    """Punto (lat, lon) de una medida M sobre la trayectoria LRS; None si queda fuera."""
    for path in route.paths:
        for first, second in zip(path, path[1:], strict=False):
            if first[2] is None or second[2] is None:
                continue
            low, high = sorted((first[2], second[2]))
            if low <= milepost <= high:
                lon, lat, _ = _at_measure(first, second, milepost)
                return round(lat, 6), round(lon, 6)
    return None


def jurisdiction(road: RoadMatch | None, location: MapLocation) -> Jurisdiction:
    """Tabla de prioridad documentada; las vías locales son una aproximación hasta M5."""
    if road is None:
        return Jurisdiction(
            authority="UNKNOWN", basis="no_road", confidence="low", note="No hay vía cercana."
        )
    if road.kind == "state":
        return Jurisdiction(
            authority="FDOT",
            name="FDOT",
            basis="state_road",
            confidence="high",
            note="Vía estatal según FDOT.",
        )
    if road.kind == "county":
        return Jurisdiction(
            authority="COUNTY",
            name=location.county,
            basis="county_road",
            confidence="medium",
            note="Aproximación: confirmar con el condado.",
        )
    if location.city:
        return Jurisdiction(
            authority="CITY",
            name=location.city,
            basis="inside_city",
            confidence="low",
            note="Aproximación: confirmar con la ciudad.",
        )
    return Jurisdiction(
        authority="COUNTY",
        name=location.county,
        basis="unincorporated",
        confidence="low",
        note="Aproximación: confirmar con el condado.",
    )


def pick_segment_road(start: list[RoadMatch], end: list[RoadMatch]) -> RoadMatch | None:
    """Vía común: estatal, condado, otra; después por cercanía total."""
    end_by_id = {road.roadway_id: road for road in end}
    candidates = [
        (road, end_by_id[road.roadway_id]) for road in start if road.roadway_id in end_by_id
    ]
    if not candidates:
        return None
    rank = {"state": 0, "county": 1, "other": 2}
    candidates.sort(key=lambda item: (rank[item[0].kind], item[0].distance_m + item[1].distance_m))
    return candidates[0][0]


def haversine_miles(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> float:
    """Distancia de seguridad antes de consultar un tramo demasiado largo."""
    radius = 3958.7613
    lat_delta = math.radians(end_lat - start_lat)
    lon_delta = math.radians(end_lon - start_lon)
    a = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(math.radians(start_lat))
        * math.cos(math.radians(end_lat))
        * math.sin(lon_delta / 2) ** 2
    )
    return radius * 2 * math.asin(math.sqrt(a))


def geometry_miles(coordinates: list[list[float]]) -> float:
    """Longitud de una LineString LRS `[lon, lat]`; no usa la línea manual del usuario."""
    return sum(
        haversine_miles(first[1], first[0], second[1], second[0])
        for first, second in zip(coordinates, coordinates[1:], strict=False)
    )


def _projection(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> tuple[float, float]:
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    ratio = 0.0 if length == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
    cx, cy = ax + ratio * dx, ay + ratio * dy
    return ratio, (px - cx) ** 2 + (py - cy) ** 2


def _slice_path(
    path: tuple[tuple[float, float, float | None], ...], low: float, high: float
) -> list[tuple[float, float, float | None]]:
    result: list[tuple[float, float, float | None]] = []
    for first, second in zip(path, path[1:], strict=False):
        if first[2] is None or second[2] is None:
            continue
        segment_low, segment_high = sorted((first[2], second[2]))
        if segment_high < low or segment_low > high:
            continue
        result.extend((_at_measure(first, second, low), _at_measure(first, second, high)))
    return list(dict.fromkeys(result))


def _at_measure(
    first: tuple[float, float, float | None],
    second: tuple[float, float, float | None],
    measure: float,
) -> tuple[float, float, float]:
    first_m, second_m = first[2], second[2]
    assert first_m is not None and second_m is not None
    ratio = (
        0 if first_m == second_m else max(0.0, min(1.0, (measure - first_m) / (second_m - first_m)))
    )
    return (
        first[0] + ratio * (second[0] - first[0]),
        first[1] + ratio * (second[1] - first[1]),
        measure,
    )
