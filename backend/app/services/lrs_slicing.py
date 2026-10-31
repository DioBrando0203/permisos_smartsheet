"""Recorte continuo por medidas M de todas las trayectorias LRS, sin inventar enlaces."""

import math
from dataclasses import dataclass

Vertex = tuple[float, float, float | None]
Paths = tuple[tuple[Vertex, ...], ...]
MEASURE_TOLERANCE = 0.00051  # Los MPs del contrato se redondean a tres decimales.
JOIN_METERS = 2.0


@dataclass(frozen=True)
class _Segment:
    first: tuple[float, float, float]
    last: tuple[float, float, float]


def at_measure(first: Vertex, second: Vertex, measure: float) -> tuple[float, float, float]:
    """Interpola y conserva la medida real al limitar a los extremos de un segmento."""
    first_m, second_m = first[2], second[2]
    assert first_m is not None and second_m is not None
    ratio = (
        0 if first_m == second_m else max(0.0, min(1.0, (measure - first_m) / (second_m - first_m)))
    )
    return (
        first[0] + ratio * (second[0] - first[0]),
        first[1] + ratio * (second[1] - first[1]),
        first_m + ratio * (second_m - first_m),
    )


def slice_paths(paths: Paths, begin: float, end: float) -> list[list[float]]:
    """Devuelve todo el rango continuo, o vacío si faltan medidas/geometría intermedia."""
    low, high = sorted((begin, end))
    if high <= low:
        return []
    segments = _segments(paths)
    cursor, result = low, []
    while segments:
        candidates = [
            segment
            for segment in segments
            if segment.first[2] <= cursor + MEASURE_TOLERANCE
            and segment.last[2] > cursor
            and (
                not result
                or _meters(result[-1], at_measure(segment.first, segment.last, cursor))
                <= JOIN_METERS
            )
        ]
        if not candidates:
            break
        segment = max(candidates, key=lambda item: item.last[2])
        first = at_measure(segment.first, segment.last, cursor)
        last = at_measure(segment.first, segment.last, high)
        if not result:
            result.append(first)
        result.append(last)
        cursor = last[2]
        segments.remove(segment)
        if cursor >= high - 1e-9:
            break
    if cursor < high - MEASURE_TOLERANCE or len(result) < 2:
        return []
    coordinates = [[round(point[0], 6), round(point[1], 6)] for point in result]
    return [
        point
        for index, point in enumerate(coordinates)
        if index == 0 or point != coordinates[index - 1]
    ]


def _segments(paths: Paths) -> list[_Segment]:
    result = []
    for path in paths:
        for a, b in zip(path, path[1:], strict=False):
            if (
                a[2] is None
                or b[2] is None
                or not math.isfinite(a[2])
                or not math.isfinite(b[2])
                or a[2] == b[2]
            ):
                continue
            first, last = sorted((a, b), key=lambda point: point[2])
            result.append(_Segment(first, last))
    return result


def _meters(a: Vertex, b: Vertex) -> float:
    scale = math.cos(math.radians((a[1] + b[1]) / 2))
    return 111_195 * math.hypot((a[0] - b[0]) * scale, a[1] - b[1])
