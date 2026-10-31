"""Selección del modo de análisis de trazo y respaldo estricto, sin E/S."""

from dataclasses import dataclass
from typing import Literal

from app.services.map_rules import RouteGeometry
from app.services.trace_alignment import align_trace
from app.services.trace_rules import Point, Run, densify, path_meters, runs, unmatched_meters

AlignmentStatus = Literal["strict", "adjusted", "ambiguous", "unavailable"]


@dataclass(frozen=True)
class TraceAnalysis:
    runs: list[Run]
    input_m: float
    unmatched_m: float
    status: AlignmentStatus
    points: list[Point]
    notes: list[str]
    coverage_radius_m: float


def analyze_trace(
    path: list[Point],
    routes: dict[str, RouteGeometry],
    radius: float,
    snap: bool,
    preferred: frozenset[str] = frozenset(),
) -> TraceAnalysis:
    """Ajustar vértices sobre la red o mantener el resultado estricto con aviso de respaldo."""
    coverage_radius = min(25, radius) if snap else radius
    samples = densify(path)
    unmatched = unmatched_meters(samples, routes, coverage_radius)
    notes = []
    if snap:
        preferred_routes = {
            identity: route for identity, route in routes.items() if identity in preferred
        }
        aligned = align_trace(path, preferred_routes, radius) if preferred_routes else None
        if aligned is None:
            aligned = align_trace(path, routes, radius)
        if aligned is not None and aligned.runs:
            if aligned.inferred:
                notes.append("TRACE_CONNECTIONS_INFERRED")
            if aligned.ambiguous:
                notes.append("TRACE_ALIGNMENT_AMBIGUOUS")
            return TraceAnalysis(
                aligned.runs,
                path_meters(path),
                unmatched,
                "ambiguous" if aligned.ambiguous else "adjusted",
                aligned.points,
                notes,
                coverage_radius,
            )
        notes.append("TRACE_ALIGNMENT_UNAVAILABLE")
    if unmatched > 0.1:
        notes.append("TRACE_PARTIAL")
    return TraceAnalysis(
        runs(samples, routes, coverage_radius),
        path_meters(path),
        unmatched,
        "unavailable" if snap else "strict",
        [],
        notes,
        coverage_radius,
    )
