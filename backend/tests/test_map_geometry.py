from app.services.map_geometry import bounds_of, closest_points, contains, nearest_vertex

SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
HOLE = [(4.0, 4.0), (6.0, 4.0), (6.0, 6.0), (4.0, 6.0), (4.0, 4.0)]


def test_contains_respects_holes() -> None:
    assert contains([SQUARE], 2, 2)
    assert not contains([SQUARE], 11, 2)
    assert not contains([SQUARE, HOLE], 5, 5)
    assert bounds_of([SQUARE]) == (0.0, 0.0, 10.0, 10.0)


def test_closest_points_finds_the_exact_crossing() -> None:
    east_west = [[(-80.27, 26.0), (-80.25, 26.0)]]
    north_south = [[(-80.26, 25.99), (-80.26, 26.01)]]
    assert closest_points(east_west, north_south) == (26.0, -80.26, 0.0)


def test_closest_points_of_parallel_streets_gives_the_distance() -> None:
    first = [[(-80.27, 26.0), (-80.25, 26.0)]]
    second = [[(-80.27, 26.001), (-80.25, 26.001)]]  # 0.001 grados de latitud: unos 111 m
    lat, _, meters = closest_points(first, second) or (0, 0, 0)
    assert 110 < meters < 112 and 26.0 < lat < 26.001


def test_nearest_vertex_picks_the_part_of_the_street_in_the_zone() -> None:
    street = [[(-80.30, 26.0), (-80.20, 26.0), (-80.10, 26.0)]]
    assert nearest_vertex(street, -80.11, 26.0) == (-80.10, 26.0)
    assert nearest_vertex([], 0, 0) is None
