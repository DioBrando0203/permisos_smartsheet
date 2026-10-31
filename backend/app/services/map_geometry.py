"""Geometría plana pura del buscador: contornos, contención y cruce entre dos calles (sin E/S)."""

import math

Point = tuple[float, float]  # (lon, lat), como lo entrega ArcGIS en WGS84
Line = list[Point]
Box = tuple[float, float, float, float]  # (oeste, sur, este, norte)
METERS_PER_DEGREE = 111_320


def bounds_of(rings: list[Line]) -> Box | None:
    xs = [point[0] for ring in rings for point in ring]
    ys = [point[1] for ring in rings for point in ring]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def contains(rings: list[Line], lon: float, lat: float) -> bool:
    """Regla par-impar sobre todos los anillos: respeta huecos (islas, enclaves)."""
    inside = False
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1], strict=False):
            if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def nearest_vertex(lines: list[Line], lon: float, lat: float) -> Point | None:
    """Vértice más cercano a un punto: lleva a la parte de la calle que está en la zona elegida."""
    points = [point for line in lines for point in line]
    return min(points, key=lambda point: _distance((lon, lat), point)) if points else None


def closest_points(lines_a: list[Line], lines_b: list[Line]) -> tuple[float, float, float] | None:
    """(lat, lon, metros) donde dos calles se cruzan (0 m) o donde están más cerca.

    Proyección local (longitud escalada por el coseno de la latitud): a escala de una ciudad el
    error es despreciable frente al ancho de una calle.
    """
    best: tuple[Point, float] | None = None
    for line_a in lines_a:
        box_a = bounds_of([line_a])
        for line_b in lines_b:
            if box_a is None or (best and _box_gap(box_a, bounds_of([line_b])) > best[1]):
                continue
            for a1, a2 in zip(line_a, line_a[1:], strict=False):
                for b1, b2 in zip(line_b, line_b[1:], strict=False):
                    point, gap = _segments(a1, a2, b1, b2)
                    if best is None or gap < best[1]:
                        best = (point, gap)
    if best is None:
        return None
    (lon, lat), gap = best
    return round(lat, 6), round(lon, 6), round(gap * METERS_PER_DEGREE, 1)


def _segments(a1: Point, a2: Point, b1: Point, b2: Point) -> tuple[Point, float]:
    """Punto de cruce de dos segmentos, o el punto medio entre sus puntos más cercanos."""
    scale = math.cos(math.radians((a1[1] + b1[1]) / 2))
    p, r = _local(a1, scale), _sub(_local(a2, scale), _local(a1, scale))
    q, s = _local(b1, scale), _sub(_local(b2, scale), _local(b1, scale))
    denominator = _cross(r, s)
    if denominator:
        t, u = _cross(_sub(q, p), s) / denominator, _cross(_sub(q, p), r) / denominator
        if 0 <= t <= 1 and 0 <= u <= 1:
            return (a1[0] + t * (a2[0] - a1[0]), a1[1] + t * (a2[1] - a1[1])), 0.0
    pairs = [(a1, _on_segment(a1, b1, b2)), (a2, _on_segment(a2, b1, b2))]
    pairs += [(_on_segment(b1, a1, a2), b1), (_on_segment(b2, a1, a2), b2)]
    first, second = min(pairs, key=lambda pair: _distance(*pair))
    middle = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
    return middle, _distance(first, second)


def _on_segment(point: Point, start: Point, end: Point) -> Point:
    scale = math.cos(math.radians(point[1]))
    dx, dy = (end[0] - start[0]) * scale, end[1] - start[1]
    length = dx * dx + dy * dy
    ratio = 0.0
    if length:
        ratio = ((point[0] - start[0]) * scale * dx + (point[1] - start[1]) * dy) / length
    ratio = max(0.0, min(1.0, ratio))
    return start[0] + ratio * (end[0] - start[0]), start[1] + ratio * (end[1] - start[1])


def _distance(first: Point, second: Point) -> float:
    """Distancia en grados de latitud equivalentes (multiplicar por METERS_PER_DEGREE)."""
    scale = math.cos(math.radians((first[1] + second[1]) / 2))
    return math.hypot((first[0] - second[0]) * scale, first[1] - second[1])


def _box_gap(first: Box, second: Box | None) -> float:
    if second is None:
        return math.inf
    dx = max(0.0, second[0] - first[2], first[0] - second[2])
    dy = max(0.0, second[1] - first[3], first[1] - second[3])
    return math.hypot(dx * math.cos(math.radians(first[1])), dy)


def _local(point: Point, scale: float) -> Point:
    return point[0] * scale, point[1]


def _sub(first: Point, second: Point) -> Point:
    return first[0] - second[0], first[1] - second[1]


def _cross(first: Point, second: Point) -> float:
    return first[0] * second[1] - first[1] * second[0]
