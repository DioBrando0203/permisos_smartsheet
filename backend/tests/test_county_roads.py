"""Adaptador de St. Johns y lugares censales (PEN-40, SPEC-B14 CA-30 y CA-31)."""

import pytest

from app.models.map import MapLocation, RoadMatch
from app.services.county_roads import (
    ST_JOHNS_MAINTAINERS,
    county_adapter,
    nearest_street,
    street_jurisdiction,
)
from app.services.map_mappers import build_location
from app.services.map_rules import jurisdiction
from tests.conftest import make_settings

LAT, LON = 30.0, -81.5
METER = 1 / 111_195
ST_JOHNS = MapLocation(county="St. Johns", county_code_fdot="78")


def _street(maintainer: str, meters: float, name: str = "Synthetic Rd", gated: str = "N") -> dict:
    """Tramo horizontal a `meters` metros al norte del punto."""
    lat = LAT + meters * METER
    return {
        "attributes": {"NAME": name, "MAINTENANCE": maintainer, "GATED": gated},
        "geometry": {"paths": [[[LON - 0.001, lat], [LON + 0.001, lat]]]},
    }


def _road(kind: str, meters: float) -> RoadMatch:
    return RoadMatch(roadway_id="78000001", kind=kind, distance_m=meters)


def _resolve(features: list[dict], roads: list[RoadMatch] | None = None):
    adapter = county_adapter(make_settings(), "78")
    assert adapter is not None
    street = nearest_street(adapter, features, LAT, LON)
    return street_jurisdiction(roads or [], ST_JOHNS, street)


def _boundaries(city: dict) -> dict:
    return {"fdot_counties": [], "fdot_cities": [{"attributes": city}], "fdot_zip": []}


def test_census_place_is_not_a_city_and_its_streets_are_unincorporated() -> None:
    location = build_location(_boundaries({"NAME": "Nocatee", "CLASSFP": "U2"}))
    assert (location.city, location.place) == (None, "Nocatee")
    assert jurisdiction(_road("other", 5), location).basis == "unincorporated"
    city = build_location(_boundaries({"NAME": "St. Augustine", "CLASSFP": "C1"}))
    assert (city.city, city.place) == ("St. Augustine", None)
    # Sin CLASSFP (fuente antigua o simulada) el nombre se conserva como ciudad.
    assert build_location(_boundaries({"NAME": "Miami"})).city == "Miami"


@pytest.mark.parametrize(
    ("lsad", "kind", "authority", "name"),
    [
        ("25", "city", "CITY", "City of Sample"),
        ("43", "town", "TOWN", "Town of Sample"),
        ("47", "village", "VILLAGE", "Village of Sample"),
    ],
)
def test_municipality_type_separates_city_town_and_village(
    lsad: str, kind: str, authority: str, name: str
) -> None:
    location = build_location(_boundaries({"NAME": "Sample", "CLASSFP": "C1", "LSAD": lsad}))
    assert location.municipality_type == kind
    result = jurisdiction(_road("other", 5), location)
    assert (result.authority, result.name, result.basis) == (authority, name, "inside_city")
    # Un lugar censal no tiene tipo de municipio; el condado lleva "County".
    place = build_location(_boundaries({"NAME": "Nocatee", "CLASSFP": "U2", "LSAD": "57"}))
    assert place.municipality_type is None
    county = jurisdiction(_road("other", 5), place.model_copy(update={"county": "St. Johns"}))
    assert county.name == "St. Johns County"


@pytest.mark.parametrize(("maintainer", "expected"), list(ST_JOHNS_MAINTAINERS.items()))
def test_each_maintainer_value_gives_its_authority(maintainer: str, expected: tuple) -> None:
    # Con una vía estatal del FDOT lejos, para que "State of Florida" quede confirmada.
    result = _resolve([_street(maintainer, 3)], [_road("state", 20)])
    assert (result.authority, result.name) == expected
    assert (result.basis, result.confidence) == ("county_maintenance", "high")
    assert f"«{maintainer}»" in result.note


def test_nearest_street_with_a_known_maintainer_wins() -> None:
    features = [
        _street("Proposed", 1, "Future Rd"),
        _street("St Johns County", 10, "County Rd"),
        _street("Private", 5, "Private Rd"),
    ]
    result = _resolve(features)
    assert result.authority == "PRIVATE"
    assert "Private Rd" in result.note


def test_unknown_values_or_no_street_fall_back_to_the_approximation() -> None:
    result = _resolve([_street("Out of County", 2), _street("", 3)], [_road("other", 4)])
    assert (result.basis, result.confidence) == ("unincorporated", "low")
    assert _resolve([]).basis == "no_road"


def test_state_by_the_county_without_an_fdot_state_road_is_medium() -> None:
    result = _resolve([_street("State of Florida", 3)], [_road("other", 2)])
    assert (result.authority, result.confidence) == ("FDOT", "medium")
    assert "confirmar" in result.note


def test_closer_fdot_state_road_keeps_the_state_rule_and_tells_the_county_value() -> None:
    result = _resolve([_street("Private", 8, "Driveway")], [_road("state", 3)])
    assert (result.authority, result.basis, result.confidence) == ("FDOT", "state_road", "high")
    assert "Driveway" in result.note and "«Private»" in result.note
    # Si el tramo del condado está más cerca, gana el condado.
    assert _resolve([_street("Private", 2)], [_road("state", 6)]).authority == "PRIVATE"


def test_gated_street_is_said_in_the_note() -> None:
    assert "(con portón)" in _resolve([_street("Private", 2, gated="Y")]).note


def test_only_st_johns_has_an_adapter() -> None:
    settings = make_settings()
    assert county_adapter(settings, "87") is None
    assert county_adapter(settings, None) is None
