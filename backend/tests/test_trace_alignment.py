"""Ajuste real de recorrido sobre redes sintéticas: curvas, desvíos, conexiones y ambigüedad."""

import pytest

from app.services.map_rules import RouteGeometry, slice_route
from app.services.trace_alignment import align_trace
from app.services.trace_analysis import analyze_trace
from app.services.trace_rules import path_meters


def route(identity, points):
    return RouteGeometry(identity, (tuple(points),))


STRAIGHT = {"A": route("A", [(-80.0, 26.0, 0.0), (-80.0, 26.01, 0.7)])}


def test_moves_a_parallel_drawing_sideways_and_shortens_its_zigzags() -> None:
    path = [(26.001, -80.0004), (26.003, -79.9995), (26.006, -80.0005), (26.009, -80.0004)]
    result = align_trace(path, STRAIGHT, 100)
    assert result is not None
    assert [run.roadway_id for run in result.runs] == ["A"]
    assert all(lon == -80 for _, lon in result.points)
    assert sum(run.length_m for run in result.runs) < path_meters(path)


def test_follows_a_curve_even_when_the_input_cuts_across_its_inside() -> None:
    curved = {"A": route("A", [(-80.0, 26.0, 0.0), (-79.999, 26.005, 0.35), (-80.0, 26.01, 0.7)])}
    path = [(26.0, -80.0), (26.01, -80.0)]
    result = align_trace(path, curved, 100)
    assert result is not None
    assert len(result.runs) == 1
    run = result.runs[0]
    assert run.length_m > path_meters(path)
    assert [-79.999, 26.005] in slice_route(curved["A"], run.begin_milepost, run.end_milepost)


def test_adds_an_intermediate_road_and_adjusts_each_transition_to_the_junction() -> None:
    routes = {
        "A": route("A", [(-80.0, 26.0, 0.0), (-80.0, 26.005, 0.35)]),
        "B": route("B", [(-80.0, 26.005, 0.0), (-79.995, 26.005, 0.31)]),
        "C": route("C", [(-79.995, 26.005, 0.0), (-79.995, 26.01, 0.35)]),
    }
    result = align_trace([(26.001, -80.0), (26.009, -79.995)], routes, 100)
    assert result is not None
    assert [run.roadway_id for run in result.runs] == ["A", "B", "C"]
    assert result.runs[0].end_milepost == 0.35
    assert result.runs[1].begin_milepost == 0
    assert result.runs[1].end_milepost == 0.31
    assert result.runs[2].begin_milepost == 0
    assert result.inferred


def test_reverse_drawing_has_the_same_ordered_mileposts() -> None:
    points = [(26.001, -80.0004), (26.009, -80.0004)]
    forward = align_trace(points, STRAIGHT, 100)
    reverse = align_trace(points[::-1], STRAIGHT, 100)
    assert forward is not None and reverse is not None
    assert forward.runs[0].begin_milepost == reverse.runs[0].begin_milepost
    assert forward.runs[0].end_milepost == reverse.runs[0].end_milepost


def test_two_point_diagonal_finds_a_corner_with_many_short_native_segments() -> None:
    a = [(-80.0, 26.0 + index * 0.0005, index * 0.035) for index in range(11)]
    b = [(-80.0 + index * 0.0005, 26.005, index * 0.031) for index in range(13)]
    routes = {"A": route("A", a), "B": route("B", b)}
    result = align_trace([(26.0, -80.0), (26.005, -79.994)], routes, 100)
    assert result is not None
    assert [run.roadway_id for run in result.runs] == ["A", "B"]


def test_preserves_a_waypoint_that_makes_the_route_return() -> None:
    path = [(26.001, -80.0), (26.009, -80.0), (26.003, -80.0)]
    result = align_trace(path, STRAIGHT, 100)
    assert result is not None
    assert result.points == path
    assert len(result.runs) == 2


def test_does_not_join_disconnected_roads() -> None:
    routes = {
        "A": route("A", [(-80.0, 26.0, 0.0), (-80.0, 26.004, 0.3)]),
        "B": route("B", [(-80.0, 26.006, 0.0), (-80.0, 26.01, 0.3)]),
    }
    assert align_trace([(26.001, -80.0), (26.009, -80.0)], routes, 100) is None


def test_warns_of_equally_good_parallel_roads() -> None:
    routes = {**STRAIGHT, "B": route("B", [(-79.9998, 26.0, 0.0), (-79.9998, 26.01, 0.7)])}
    result = align_trace([(26.001, -79.9999), (26.009, -79.9999)], routes, 100)
    assert result is not None and result.ambiguous


def test_prefers_a_verified_state_road_over_its_auxiliary_parallel_carriageway() -> None:
    routes = {**STRAIGHT, "B": route("B", [(-79.9998, 26.0, 0.0), (-79.9998, 26.01, 0.7)])}
    path = [(26.001, -79.99975), (26.009, -79.99975)]
    result = analyze_trace(path, routes, 100, True, frozenset({"A"}))
    assert result.status == "adjusted"
    assert [run.roadway_id for run in result.runs] == ["A"]


@pytest.mark.parametrize(
    "path",
    [
        [(26.001, -80.0), (26.009, -79.99)],
        [(26.001, -80.0), (26.005, -79.99), (26.009, -80.0)],
    ],
)
def test_does_not_ignore_an_endpoint_or_waypoint_outside_tolerance(path) -> None:
    assert align_trace(path, STRAIGHT, 100) is None
