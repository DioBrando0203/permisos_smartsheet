"""Presentación del análisis de trazo en el contrato HTTP, sin consultar proveedores."""

from app.models.map import MapTrace, SourceStatus, TraceAdjustment, WorkLocation
from app.services.map_rules import RouteGeometry, distance_m_to_route
from app.services.trace_analysis import TraceAnalysis
from app.services.trace_rules import Point, meters_between

METERS_PER_MILE = 1609.344


def trace_response(
    path: list[Point],
    rows: list[WorkLocation],
    sources: list[SourceStatus],
    analysis: TraceAnalysis,
    radius: float,
) -> MapTrace:
    warnings = list(analysis.notes)
    if any(source.status != "ok" for source in sources):
        warnings.append("SOURCE_FAILED")
    if not rows:
        warnings.append("NO_ROAD_NEARBY")
    if any(row.kind != "state" for row in rows):
        warnings.append("NOT_STATE_ROAD")
    incomplete = any(row.length_mi is None for row in rows)
    if incomplete:
        warnings.append("TRACE_GEOMETRY_INCOMPLETE")
    return MapTrace(
        path=[[round(lat, 6), round(lon, 6)] for lat, lon in path],
        input_length_mi=round(analysis.input_m / METERS_PER_MILE, 3),
        length_mi=None if incomplete else round(sum(row.length_mi or 0 for row in rows), 3),
        matched_percent=round(
            100 * max(0, analysis.input_m - analysis.unmatched_m) / analysis.input_m, 1
        )
        if analysis.input_m
        else 0,
        unmatched_length_mi=round(analysis.unmatched_m / METERS_PER_MILE, 3),
        alignment=analysis.status,
        radius_m=radius,
        coverage_radius_m=analysis.coverage_radius_m,
        snapped_points=[[round(lat, 6), round(lon, 6)] for lat, lon in analysis.points],
        rows=rows,
        sources=sources,
        warnings=warnings,
    )


def endpoint_adjustment(
    path: list[Point], analysis: TraceAnalysis, routes: dict[str, RouteGeometry]
) -> TraceAdjustment | None:
    if analysis.points:
        return TraceAdjustment(
            start_m=round(meters_between(path[0], analysis.points[0]), 1),
            end_m=round(meters_between(path[-1], analysis.points[-1]), 1),
        )
    if not analysis.runs:
        return None
    first, last = routes[analysis.runs[0].roadway_id], routes[analysis.runs[-1].roadway_id]
    return TraceAdjustment(
        start_m=distance_m_to_route(*path[0], first), end_m=distance_m_to_route(*path[-1], last)
    )
