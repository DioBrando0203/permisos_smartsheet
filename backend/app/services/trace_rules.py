"""Reglas puras del trazo (PEN-32): de una línea dibujada a filas de Work Location, como OSP.

El trazo se recorre cada `SAMPLE_METERS` y cada muestra queda en la vía más cercana dentro del
radio. Mientras la vía actual siga dentro del radio no se cambia de vía: así un cruce no corta
la fila. Los tramos más cortos que `MIN_RUN_METERS` se descartan (rozar una esquina).
"""

import math
import re
from dataclasses import dataclass

from app.services.map_rules import RouteGeometry, distance_m_to_route, milepost_at

Point = tuple[float, float]  # (lat, lon)
Box = tuple[float, float, float, float]  # (oeste, sur, este, norte)
SAMPLE_METERS = 10.0
MIN_RUN_METERS = 20.0
_EARTH_METERS = 6_371_008.8
_PAIR = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


@dataclass(frozen=True)
class Run:
    """Tramo del trazo sobre una vía, con sus mileposts ordenados."""

    roadway_id: str
    begin_milepost: float
    end_milepost: float
    length_m: float


def parse_path(text: str) -> list[Point] | None:
    """`lat,lon;lat,lon;…` (6 decimales como la URL del panel); None si algo no es un par."""
    points = []
    for part in text.split(";"):
        match = _PAIR.match(part)
        if not match:
            return None
        points.append((float(match[1]), float(match[2])))
    return points


def meters_between(a: Point, b: Point) -> float:
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat, dlon = lat2 - lat1, math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_METERS * math.asin(math.sqrt(h))


def path_meters(path: list[Point]) -> float:
    return sum(meters_between(a, b) for a, b in zip(path, path[1:], strict=False))


def densify(path: list[Point], step: float = SAMPLE_METERS) -> list[Point]:
    """Muestras separadas `step` metros como máximo, con los vértices del trazo incluidos."""
    samples = path[:1]
    for (lat1, lon1), (lat2, lon2) in zip(path, path[1:], strict=False):
        count = max(1, math.ceil(meters_between((lat1, lon1), (lat2, lon2)) / step))
        samples += [
            (lat1 + (lat2 - lat1) * i / count, lon1 + (lon2 - lon1) * i / count)
            for i in range(1, count + 1)
        ]
    return samples


def envelopes(path: list[Point], radius_m: float, chunk_m: float = 300.0) -> list[Box]:
    """Rectángulos que cubren el trazo más el radio, en trozos cortos.

    Un solo rectángulo para un trazo en diagonal traería cientos de calles que no toca.
    """
    samples = densify(path)
    size = max(1, int(chunk_m / SAMPLE_METERS))
    boxes = []
    for start in range(0, max(1, len(samples) - 1), size):
        chunk = samples[start : start + size + 1]
        lats, lons = [p[0] for p in chunk], [p[1] for p in chunk]
        dlat = radius_m / 111_320
        dlon = dlat / math.cos(math.radians(sum(lats) / len(lats)))
        boxes.append((min(lons) - dlon, min(lats) - dlat, max(lons) + dlon, max(lats) + dlat))
    return boxes


def runs(samples: list[Point], routes: dict[str, RouteGeometry], radius_m: float) -> list[Run]:
    """Una fila por cada vía que sigue el trazo, en el orden en que se recorre."""
    near = [_near(point, routes, radius_m) for point in samples]
    kept: list[tuple[str, int, int]] = []
    for roadway, first, last in _groups(near):
        if path_meters(samples[first : last + 1]) < MIN_RUN_METERS:
            continue
        if kept and kept[-1][0] == roadway:
            # La misma vía a ambos lados de un tramo descartado: una sola fila.
            kept[-1] = (roadway, kept[-1][1], last)
        else:
            kept.append((roadway, first, last))
    result = []
    for roadway, first, last in kept:
        mileposts = _mileposts(samples, near, roadway, first, last, routes[roadway])
        if mileposts:
            length = round(path_meters(samples[first : last + 1]), 1)
            result.append(Run(roadway, *mileposts, length))
    return result


def _near(point: Point, routes: dict[str, RouteGeometry], radius_m: float) -> dict[str, float]:
    found = {}
    for roadway, route in routes.items():
        distance = distance_m_to_route(point[0], point[1], route)
        if distance is not None and distance <= radius_m:
            found[roadway] = distance
    return found


def _groups(near: list[dict[str, float]]) -> list[tuple[str, int, int]]:
    """Muestras consecutivas de una misma vía; se sigue en la actual mientras esté en el radio."""
    groups: list[tuple[str, int, int]] = []
    current: str | None = None
    for index, found in enumerate(near):
        if current not in found:
            current = min(found, key=found.__getitem__) if found else None
        if current is None:
            continue
        if groups and groups[-1][0] == current and groups[-1][2] == index - 1:
            groups[-1] = (current, groups[-1][1], index)
        else:
            groups.append((current, index, index))
    return groups


def _mileposts(
    samples: list[Point],
    near: list[dict[str, float]],
    roadway: str,
    first: int,
    last: int,
    route: RouteGeometry,
) -> tuple[float, float] | None:
    """Mileposts de los extremos, extendidos mientras la vía siga en el radio.

    Al doblar de A a B, las muestras sobre B antes de soltar A proyectan sobre A en el cruce;
    así cada fila termina y empieza en la intersección y no unos metros después.
    """
    while first > 0 and roadway in near[first - 1]:
        first -= 1
    while last < len(samples) - 1 and roadway in near[last + 1]:
        last += 1
    start = milepost_at(samples[first][0], samples[first][1], route)
    end = milepost_at(samples[last][0], samples[last][1], route)
    if start is None or end is None:
        return None
    low, high = sorted((start, end))
    return round(low, 3), round(high, 3)
