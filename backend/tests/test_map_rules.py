import pytest

from app.models.map import MapLocation, RoadMatch
from app.services.map_rules import (
    RouteGeometry,
    distance_m_to_route,
    geometry_miles,
    haversine_miles,
    jurisdiction,
    milepost_at,
    pick_segment_road,
    point_at_milepost,
    slice_route,
)


def road(kind: str = "state") -> RoadMatch:
    return RoadMatch(roadway_id="87281000", kind=kind, distance_m=2)


def test_milepost_control_case_interpolates_lrs_route() -> None:
    route = RouteGeometry(
        "87281000", (((-80.26361, 25.771778, 3.124), (-80.264005, 25.782147, 3.839)),)
    )
    assert milepost_at(25.771778, -80.26361, route) == 3.124
    assert milepost_at(25.782147, -80.264005, route) == 3.839
    assert len(slice_route(route, 3.124, 3.839)) == 2


def test_jurisdiction_priority_table() -> None:
    location = MapLocation(county="Miami-Dade", city="Miami")
    assert jurisdiction(road("state"), location).authority == "FDOT"
    assert jurisdiction(road("county"), location).confidence == "medium"
    assert jurisdiction(road("other"), location).authority == "CITY"
    assert jurisdiction(road("other"), MapLocation(county="Miami-Dade")).basis == "unincorporated"
    assert jurisdiction(None, location).authority == "UNKNOWN"


def test_pick_segment_road_prefers_state_then_distance() -> None:
    state = road("state")
    county = RoadMatch(roadway_id="county", kind="county", distance_m=0)
    assert pick_segment_road([county, state], [county, state]) == state


def test_point_at_milepost_interpolates_and_rejects_out_of_range() -> None:
    route = RouteGeometry(
        "87281000", (((-80.26361, 25.771778, 3.124), (-80.264005, 25.782147, 3.839)),)
    )
    assert point_at_milepost(route, 3.124) == (25.771778, -80.26361)
    lat, lon = point_at_milepost(route, 3.5) or (0, 0)
    assert 25.771778 < lat < 25.782147 and -80.264005 < lon < -80.26361
    assert point_at_milepost(route, 9.0) is None


def test_geometry_miles_uses_the_lrs_line_not_the_input_trace() -> None:
    geometry = [[-80.26361, 25.771778], [-80.264005, 25.782147]]
    assert geometry_miles(geometry) == haversine_miles(25.771778, -80.26361, 25.782147, -80.264005)


@pytest.mark.parametrize("reverse", [False, True])
def test_slice_joins_all_multipart_lrs_fragments_in_measure_order(reverse: bool) -> None:
    first = ((-80.0, 26.0, 0.0), (-80.0, 26.005, 0.5))
    second = ((-80.0, 26.005, 0.5), (-80.0, 26.01, 1.0))
    paths = (second[::-1], first[::-1], second) if reverse else (first, second, first)
    route = RouteGeometry("synthetic", paths)
    assert slice_route(route, 0.2, 0.8) == [[-80.0, 26.002], [-80.0, 26.005], [-80.0, 26.008]]
    assert slice_route(route, 0.8, 0.2) == slice_route(route, 0.2, 0.8)


def test_slice_clips_overlapping_fragments_without_backtracking() -> None:
    route = RouteGeometry(
        "synthetic",
        (
            ((-80.0, 26.0, 0.0), (-80.0, 26.006, 0.6)),
            ((-80.0, 26.004, 0.4), (-80.0, 26.01, 1.0)),
        ),
    )
    assert slice_route(route, 0.2, 0.8) == [[-80.0, 26.002], [-80.0, 26.006], [-80.0, 26.008]]


@pytest.mark.parametrize(
    "paths",
    [
        (((-80.0, 26.0, 0.0), (-80.0, 26.005, 0.5)),),  # Falta el final.
        (((-80.0, 26.005, 0.5), (-80.0, 26.01, 1.0)),),  # Falta el principio.
        (((-80.0, 26.0, None), (-80.0, 26.01, 1.0)),),  # Sin medidas.
        (
            ((-80.0, 26.0, 0.0), (-80.0, 26.004, 0.4)),
            ((-80.0, 26.006, 0.6), (-80.0, 26.01, 1.0)),
        ),  # Hueco de medidas.
        (
            ((-80.0, 26.0, 0.0), (-80.0, 26.005, 0.5)),
            ((-80.001, 26.005, 0.5), (-80.001, 26.01, 1.0)),
        ),  # Hueco espacial.
    ],
)
def test_slice_does_not_invent_geometry_for_a_missing_part(paths) -> None:
    assert slice_route(RouteGeometry("synthetic", paths), 0.2, 0.8) == []


def test_distance_to_lrs_uses_longitude_scale_at_florida_latitude() -> None:
    route = RouteGeometry("synthetic", (((-80.0, 26.0, 0.0), (-80.0, 26.01, 1.0)),))
    expected = haversine_miles(26.005, -79.9998, 26.005, -80.0) * 1609.344
    assert distance_m_to_route(26.005, -79.9998, route) == pytest.approx(expected, abs=0.1)
