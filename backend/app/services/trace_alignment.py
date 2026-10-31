"""Ajuste de los vértices dibujados a un recorrido continuo LRS; sin acceso a OSP."""

import heapq
from dataclasses import dataclass

from app.services.map_rules import RouteGeometry
from app.services.trace_network import Edge, Network, build_network
from app.services.trace_rules import Point, Run, path_meters


@dataclass(frozen=True)
class Alignment:
    runs: list[Run]
    points: list[Point]
    ambiguous: bool
    inferred: bool


@dataclass(frozen=True)
class _Plan:
    cost: float
    steps: list[Edge]
    points: list[Point]


def align_trace(
    path: list[Point], routes: dict[str, RouteGeometry], radius: float
) -> Alignment | None:
    """Respeta orden de vértices y continuidad; devuelve None si no hay solución local."""
    network = build_network(path, routes, radius)
    if network is None:
        return None
    plans = {
        a.node: _Plan(a.distance_m * 2, [], [network.points[a.node]]) for a in network.anchors[0]
    }
    for candidates in network.anchors[1:]:
        distances, previous = _search(network, plans)
        next_plans = {}
        for candidate in candidates:
            if candidate.node not in distances:
                continue
            source, steps = _backtrack(candidate.node, previous)
            prefix = plans[source]
            next_plans[candidate.node] = _Plan(
                distances[candidate.node] + candidate.distance_m * 2,
                prefix.steps + steps,
                prefix.points + [network.points[candidate.node]],
            )
        plans = next_plans
        if not plans:
            return None
    valid = sorted(
        (plan for plan in plans.values() if _acceptable(plan, path, radius)), key=lambda p: p.cost
    )
    if not valid:
        return None
    best = valid[0]
    found = _runs(best.steps)
    ambiguous = any(
        plan.cost - best.cost <= max(5, best.cost * 0.03)
        and _signature(_runs(plan.steps)) != _signature(found)
        for plan in valid[1:]
    )
    return Alignment(found, best.points, ambiguous, any(step.inferred for step in best.steps))


def _search(
    network: Network, plans: dict[int, _Plan]
) -> tuple[dict[int, float], dict[int, tuple[int, Edge] | None]]:
    distances = {node: plan.cost for node, plan in plans.items()}
    previous: dict[int, tuple[int, Edge] | None] = {node: None for node in plans}
    queue = [(cost, node) for node, cost in distances.items()]
    heapq.heapify(queue)
    while queue:
        cost, node = heapq.heappop(queue)
        if cost > distances[node]:
            continue
        for edge in network.edges[node]:
            candidate = cost + edge.cost
            if candidate + 1e-8 < distances.get(edge.target, float("inf")):
                distances[edge.target] = candidate
                previous[edge.target] = node, edge
                heapq.heappush(queue, (candidate, edge.target))
    return distances, previous


def _backtrack(node: int, previous: dict[int, tuple[int, Edge] | None]) -> tuple[int, list[Edge]]:
    result = []
    while previous[node] is not None:
        parent, edge = previous[node]
        result.append(edge)
        node = parent
    return node, list(reversed(result))


def _acceptable(plan: _Plan, path: list[Point], radius: float) -> bool:
    length = sum(step.meters for step in plan.steps)
    return 1 <= length <= path_meters(path) * 2.5 + radius * 2


def _runs(steps: list[Edge]) -> list[Run]:
    """Una fila por vía continua; conserva la dirección hasta terminar la agrupación."""
    grouped: list[tuple[str, float, float, float]] = []
    for step in steps:
        if step.roadway is None or step.meters < 0.01:
            continue
        if (
            grouped
            and grouped[-1][0] == step.roadway
            and abs(grouped[-1][2] - step.begin) < 0.001
            and (grouped[-1][2] - grouped[-1][1]) * (step.end - step.begin) > 0
        ):
            roadway, begin, _, length = grouped[-1]
            grouped[-1] = roadway, begin, step.end, length + step.meters
        else:
            grouped.append((step.roadway, step.begin, step.end, step.meters))
    return [
        Run(road, round(min(a, b), 3), round(max(a, b), 3), length)
        for road, a, b, length in grouped
        if round(a, 3) != round(b, 3)
    ]


def _signature(found: list[Run]) -> list[tuple[str, float, float]]:
    return [(run.roadway_id, run.begin_milepost, run.end_milepost) for run in found]
