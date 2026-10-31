"""Reglas puras del trazo (PEN-32) con dos vías sintéticas que se cruzan en 26.005, -80.000.

A va de sur a norte (milepost 0 a 0.691) y B de oeste a este (0 a 0.620); el trazo va 5 m al
este de A, como una línea dibujada a mano sobre la calle.
"""

import pytest

from app.services.map_rules import RouteGeometry
from app.services.trace_rules import (
    densify,
    envelopes,
    meters_between,
    parse_path,
    path_meters,
    runs,
    unmatched_meters,
)

ROUTES = {
    "A": RouteGeometry("A", (((-80.0, 26.000, 0.0), (-80.0, 26.010, 0.691)),)),
    "B": RouteGeometry("B", (((-80.005, 26.005, 0.0), (-79.995, 26.005, 0.620)),)),
}
EAST_OF_A = -79.99995


def _runs(path):
    return [
        (r.roadway_id, r.begin_milepost, r.end_milepost) for r in runs(densify(path), ROUTES, 25)
    ]


def test_parse_path_accepts_pairs_and_rejects_anything_else() -> None:
    assert parse_path("25.771778,-80.263610;25.782147, -80.264005") == [
        (25.771778, -80.26361),
        (25.782147, -80.264005),
    ]
    assert parse_path("25.7,-80.2;calle") is None
    assert parse_path("") is None


def test_densify_keeps_vertices_and_spacing() -> None:
    path = [(26.0, -80.0), (26.001, -80.0), (26.001, -79.998)]
    samples = densify(path)
    assert samples[0] == path[0] and samples[-1] == path[-1]
    gaps = [meters_between(a, b) for a, b in zip(samples, samples[1:], strict=False)]
    assert max(gaps) <= 10.0 + 1e-6
    assert path_meters(samples) == pytest.approx(path_meters(path))


def test_envelopes_cover_the_trace_plus_radius() -> None:
    path = [(26.0, -80.0), (26.01, -80.0)]
    boxes = envelopes(path, radius_m=25)
    assert len(boxes) >= 3
    west, south, east, north = boxes[0]
    assert south < 26.0 < north and west < -80.0 < east
    assert max(box[3] for box in boxes) > 26.01


def test_a_crossing_does_not_cut_the_row() -> None:
    rows = _runs([(26.001, EAST_OF_A), (26.009, EAST_OF_A)])
    assert [row[0] for row in rows] == ["A"]
    assert rows[0][1:] == pytest.approx((0.069, 0.622), abs=0.002)


def test_turning_onto_another_road_gives_two_rows_meeting_at_the_intersection() -> None:
    rows = _runs([(26.001, EAST_OF_A), (26.005, EAST_OF_A), (26.005, -79.997)])
    assert [row[0] for row in rows] == ["A", "B"]
    assert rows[0][1:] == pytest.approx((0.069, 0.346), abs=0.003)
    # B empieza donde el trazo (5 m al este de A) la toca: 0.62 * 0.00505 / 0.01 = 0.313.
    assert rows[1][1:] == pytest.approx((0.313, 0.496), abs=0.002)


def test_mileposts_are_ordered_even_when_drawn_backwards() -> None:
    assert _runs([(26.009, EAST_OF_A), (26.001, EAST_OF_A)]) == _runs(
        [(26.001, EAST_OF_A), (26.009, EAST_OF_A)]
    )


def test_a_trace_away_from_every_road_gives_no_rows() -> None:
    assert _runs([(26.001, -79.99), (26.002, -79.99)]) == []


def test_leaving_the_road_and_returning_does_not_silently_join_the_gap() -> None:
    path = [(26.001, -80.0), (26.004, -80.0), (26.005, -79.998), (26.006, -80.0), (26.009, -80.0)]
    routes = {"A": ROUTES["A"]}
    samples = densify(path)
    found = runs(samples, routes, 25)
    assert len(found) == 2
    assert found[0].end_milepost < found[1].begin_milepost
    assert unmatched_meters(samples, routes, 25) > 300


def test_coverage_is_complete_for_a_crooked_line_inside_the_road_radius() -> None:
    samples = densify([(26.001, -80.0001), (26.004, -79.9999), (26.009, -80.0001)])
    assert unmatched_meters(samples, {"A": ROUTES["A"]}, 25) == 0


def test_a_route_without_measure_cannot_match_a_trace() -> None:
    route = RouteGeometry("A", (((-80.0, 26.0, None), (-80.0, 26.01, None)),))
    samples = densify([(26.001, -80.0), (26.009, -80.0)])
    assert runs(samples, {"A": route}, 25) == []
    assert unmatched_meters(samples, {"A": route}, 25) == pytest.approx(path_meters(samples))
