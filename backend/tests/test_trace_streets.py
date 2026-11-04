"""Calles del condado que sigue un trazo (PEN-41, SPEC-B14 CA-34). Reglas puras."""

from app.services.county_roads import county_adapter
from app.services.trace_streets import group_streets, street_line, street_rows
from tests.conftest import make_settings

LAT, LON = 30.0, -81.5
METER = 1 / 111_195
EAST = METER / 0.866  # un metro hacia el este a 30° de latitud


def _segment(oid: str, name: str, maintainer: str, path: list[list[float]]) -> dict:
    attributes = {"OBJECTID": oid, "NAME": name, "MAINTENANCE": maintainer, "GATED": "N"}
    return {"attributes": attributes, "geometry": {"paths": [path]}}


# Calle A hacia el este 500 m; calle B hacia el norte 300 m desde su final (una esquina).
CORNER = [LON + 500 * EAST, LAT]
A = [
    _segment("1", "A Rd", "St Johns County", [[LON, LAT], [LON + 250 * EAST, LAT]]),
    _segment("2", "A Rd", "St Johns County", [[LON + 250 * EAST, LAT], CORNER]),
]
B = [_segment("3", "B Way", "Private", [CORNER, [CORNER[0], LAT + 300 * METER]])]
# Calle C cruza A por la mitad, de sur a norte.
C = [
    _segment(
        "4",
        "C St",
        "Private CDD",
        [[LON + 200 * EAST, LAT - 0.002], [LON + 200 * EAST, LAT + 0.002]],
    )
]


def _rows(features: list[dict], path: list[tuple[float, float]]):
    adapter = county_adapter(make_settings(), "78")
    assert adapter is not None
    return street_rows(adapter, group_streets(features), path, 30)


def test_trace_along_two_streets_gives_two_rows_in_order_without_cutting_at_a_crossing() -> None:
    path = [(LAT + 5 * METER, LON), (LAT + 5 * METER, CORNER[0]), (LAT + 300 * METER, CORNER[0])]
    rows, unmatched = _rows(A + B + C, path)
    assert [(row.name, row.authority) for row in rows] == [("A Rd", "COUNTY"), ("B Way", "PRIVATE")]
    # En la esquina se sigue en A mientras esté en el radio (30 m): A suma y B resta lo mismo.
    assert 0.31 < rows[0].length_mi < 0.33 and 0.15 < rows[1].length_mi < 0.18
    # Los dos tramos de A forman una sola calle y se dibujan ambos.
    assert len(rows[0].paths) == 2
    assert unmatched < 1


def test_a_short_brush_gives_no_row_and_far_from_streets_is_unmatched() -> None:
    # De sur a norte, 29 m al oeste del extremo de A: sólo unos 15 m quedan en el radio.
    path = [(LAT - 250 * METER, LON - 29 * EAST), (LAT + 250 * METER, LON - 29 * EAST)]
    rows, unmatched = _rows(A, path)
    assert rows == []
    assert unmatched > 480


def test_the_same_street_after_a_gap_is_one_row() -> None:
    bend = [
        (LAT, LON),
        (LAT, LON + 150 * EAST),
        (LAT + 80 * METER, LON + 200 * EAST),
        (LAT, LON + 250 * EAST),
        (LAT, CORNER[0]),
    ]
    rows, unmatched = _rows(A, bend)
    assert [row.name for row in rows] == ["A Rd"]
    assert unmatched > 50


def test_out_of_county_and_repeated_segments_are_skipped() -> None:
    adapter = county_adapter(make_settings(), "78")
    assert adapter is not None
    outside = _segment("9", "Far Rd", "Out of County", [[LON, LAT], [LON + 0.001, LAT]])
    assert street_line(adapter, outside) is None
    proposed = street_line(
        adapter, _segment("8", "New Rd", "Proposed", [[LON, LAT], [LON + 0.001, LAT]])
    )
    assert proposed is not None and proposed.authority is None and proposed.id == "8"
    assert set(group_streets(A + A + [outside])) == {"A Rd|St Johns County"}
