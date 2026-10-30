from app.models.map import MapLocation, RoadMatch
from app.services.map_rules import (
    RouteGeometry,
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
