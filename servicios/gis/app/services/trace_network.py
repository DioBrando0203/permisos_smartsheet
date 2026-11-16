"""Grafo local de segmentos LRS y vértices proyectados; sin HTTP ni reglas de conducción."""

import math
from dataclasses import dataclass

from app.services.map_geometry import closest_points
from app.services.map_rules import RouteGeometry, distance_m_to_route, project_segment
from app.services.trace_rules import Box, Point, envelopes, meters_between, path_meters

MAX_SEGMENTS = 800
JOIN_METERS = 2.0
CELL_METERS = 150.0
Vertex = tuple[float, float, float]


@dataclass(frozen=True)
class Segment:
    roadway: str
    first: Vertex  # lon, lat, M
    last: Vertex

    def point(self, ratio: float) -> Point:
        return (
            self.first[1] + ratio * (self.last[1] - self.first[1]),
            self.first[0] + ratio * (self.last[0] - self.first[0]),
        )

    def measure(self, ratio: float) -> float:
        return self.first[2] + ratio * (self.last[2] - self.first[2])


@dataclass(frozen=True)
class Edge:
    target: int
    roadway: str | None
    begin: float
    end: float
    meters: float
    cost: float
    inferred: bool = False


@dataclass(frozen=True)
class Anchor:
    node: int
    distance_m: float


@dataclass(frozen=True)
class Network:
    edges: dict[int, list[Edge]]
    points: dict[int, Point]
    anchors: list[list[Anchor]]


def build_network(
    path: list[Point], routes: dict[str, RouteGeometry], radius: float
) -> Network | None:
    """Red acotada alrededor del dibujo; None si algún vértice no tiene candidato."""
    boxes = envelopes(path, corridor_radius(path, radius))
    segments = _segments(routes, boxes)
    if not segments or len(segments) > MAX_SEGMENTS:
        return None
    builder = _Builder(segments)
    anchors = [builder.anchors(point, radius) for point in path]
    if any(not candidates for candidates in anchors):
        return None
    if not builder.junctions(path[0][0]):
        return None
    return builder.finish(path, radius, anchors)


def corridor_radius(path: list[Point], radius: float) -> float:
    """Amplía la búsqueda para incluir esquinas que una diagonal de dos puntos no toca."""
    return max(150, radius * 2, min(500, path_meters(path) / 2))


class _Builder:
    def __init__(self, segments: list[Segment]) -> None:
        self.segments = segments
        self.nodes: dict[tuple[int, float], int] = {}
        self.points: dict[int, Point] = {}
        self.links: list[tuple[int, int, bool]] = []
        for index in range(len(segments)):
            self.node(index, 0)
            self.node(index, 1)

    def node(self, index: int, ratio: float) -> int:
        key = index, round(ratio, 9)
        if key not in self.nodes:
            identity = len(self.nodes)
            self.nodes[key] = identity
            self.points[identity] = self.segments[index].point(ratio)
        return self.nodes[key]

    def anchors(self, point: Point, radius: float) -> list[Anchor]:
        best: dict[str, tuple[float, int, float]] = {}
        for index, segment in enumerate(self.segments):
            ratio, distance = project_segment(point, segment.point(0), segment.point(1))
            if distance <= radius and (
                segment.roadway not in best or distance < best[segment.roadway][0]
            ):
                best[segment.roadway] = distance, index, ratio
        return [
            Anchor(self.node(index, ratio), distance)
            for distance, index, ratio in sorted(best.values())[:4]
        ]

    def junctions(self, latitude: float) -> bool:
        """Índice espacial para no comparar cada segmento con toda la red."""
        grid: dict[tuple[int, int], list[int]] = {}
        checked: set[tuple[int, int]] = set()
        for index, segment in enumerate(self.segments):
            cells = _cells(segment, latitude)
            if cells is None:
                return False
            for cell in cells:
                for other in grid.get(cell, []):
                    pair = other, index
                    if pair not in checked:
                        checked.add(pair)
                        self.connect(other, index)
                grid.setdefault(cell, []).append(index)
        return True

    def connect(self, first: int, last: int) -> None:
        a, b = self.segments[first], self.segments[last]
        crossing = closest_points([[a.first[:2], a.last[:2]]], [[b.first[:2], b.last[:2]]])
        if crossing is None or crossing[2] > JOIN_METERS:
            return
        point = crossing[0], crossing[1]
        ar, _ = project_segment(point, a.point(0), a.point(1))
        br, _ = project_segment(point, b.point(0), b.point(1))
        self.links.append((self.node(first, ar), self.node(last, br), a.roadway != b.roadway))

    def finish(self, path: list[Point], radius: float, anchors: list[list[Anchor]]) -> Network:
        edges: dict[int, list[Edge]] = {node: [] for node in self.points}
        drawing = RouteGeometry("input", (tuple((lon, lat, 0.0) for lat, lon in path),))
        splits: dict[int, list[tuple[float, int]]] = {}
        for (index, ratio), node in self.nodes.items():
            splits.setdefault(index, []).append((ratio, node))
        for index, points in splits.items():
            segment = self.segments[index]
            ordered = sorted(points)
            for (ar, a), (br, b) in zip(ordered, ordered[1:], strict=False):
                length = meters_between(self.points[a], self.points[b])
                deviation = distance_m_to_route(*segment.point((ar + br) / 2), drawing) or 0
                cost = length * (1 + deviation / max(25, radius))
                begin, end = segment.measure(ar), segment.measure(br)
                edges[a].append(Edge(b, segment.roadway, begin, end, length, cost))
                edges[b].append(Edge(a, segment.roadway, end, begin, length, cost))
        for a, b, inferred in self.links:
            length = meters_between(self.points[a], self.points[b])
            edges[a].append(Edge(b, None, 0, 0, length, length, inferred))
            edges[b].append(Edge(a, None, 0, 0, length, length, inferred))
        return Network(edges, self.points, anchors)


def _segments(routes: dict[str, RouteGeometry], boxes: list[Box]) -> list[Segment]:
    result = []
    for roadway, route in sorted(routes.items()):
        for path in route.paths:
            for first, last in zip(path, path[1:], strict=False):
                if first[2] is None or last[2] is None or first[2] == last[2]:
                    continue
                if not all(math.isfinite(value) for point in (first, last) for value in point):
                    continue
                if any(_touches(first, last, box) for box in boxes):
                    result.append(Segment(roadway, first, last))
                    if len(result) > MAX_SEGMENTS:
                        return result
    return result


def _touches(first: Vertex, last: Vertex, box: Box) -> bool:
    return (
        min(first[0], last[0]) <= box[2]
        and max(first[0], last[0]) >= box[0]
        and min(first[1], last[1]) <= box[3]
        and max(first[1], last[1]) >= box[1]
    )


def _cells(segment: Segment, latitude: float) -> list[tuple[int, int]] | None:
    scale = 111_195 * math.cos(math.radians(latitude))
    xs = [point[0] * scale for point in (segment.first, segment.last)]
    ys = [point[1] * 111_195 for point in (segment.first, segment.last)]
    west, east = (
        math.floor((min(xs) - JOIN_METERS) / CELL_METERS),
        math.floor((max(xs) + JOIN_METERS) / CELL_METERS),
    )
    south, north = (
        math.floor((min(ys) - JOIN_METERS) / CELL_METERS),
        math.floor((max(ys) + JOIN_METERS) / CELL_METERS),
    )
    # Una diagonal enorme no debe llenar la memoria con celdas del rectángulo completo.
    if (east - west + 1) * (north - south + 1) > 10_000:
        return None
    return [(x, y) for x in range(west, east + 1) for y in range(south, north + 1)]
