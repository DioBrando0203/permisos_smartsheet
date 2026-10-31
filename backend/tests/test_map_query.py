from app.services.map_query import (
    RouteQuery,
    address_text,
    looks_like_address,
    name_where,
    parse_coordinates,
    parse_intersection,
    parse_route_milepost,
    route_where,
    street_rank,
    street_text,
    street_where,
    tiger_where,
)


def test_parse_coordinates_accepts_comma_or_space() -> None:
    assert parse_coordinates("25.771778, -80.263610") == (25.771778, -80.26361)
    assert parse_coordinates("25.771778 -80.263610") == (25.771778, -80.26361)
    assert parse_coordinates("200 E Las Olas Blvd") is None


def test_parse_route_milepost_variants() -> None:
    assert parse_route_milepost("SR 953 3.5") == RouteQuery("SR", "953", 3.5)
    assert parse_route_milepost("sr-953 mp 3.5") == RouteQuery("SR", "953", 3.5)
    assert parse_route_milepost("CR 811, 0.308") == RouteQuery("CR", "811", 0.308)
    assert parse_route_milepost("SR A1A MP 8.492") == RouteQuery("SR", "A1A", 8.492)
    assert parse_route_milepost("87281000 3.124") == RouteQuery("ROADWAY", "87281000", 3.124)
    assert parse_route_milepost("SR 953") is None
    assert parse_route_milepost("Lejeune Rd") is None


def test_route_where_uses_the_validated_number() -> None:
    assert route_where(RouteQuery("SR", "953", 1)) == "ROUTENUM = '953'"
    assert route_where(RouteQuery("ROADWAY", "87281000", 1)) == "ROADWAY = '87281000'"


def test_street_where_normalizes_and_never_keeps_quotes() -> None:
    assert street_where("NW 42nd Avenue") == (
        "(UPPER(NAME) LIKE 'NW 42 AVE%' OR UPPER(NAME) LIKE '% NW 42 AVE%' "
        "OR UPPER(NAME) LIKE '%/NW 42 AVE%')"
    )
    assert "LIKE 'W FLAGLER ST%'" in (street_where("W Flagler Street") or "")
    injected = street_where("O'Brien'; DROP TABLE x --")
    assert injected is not None and injected.count("'") == 6 and "O BRIEN" in injected
    assert street_where("ab") is None


def test_address_detection_and_state() -> None:
    assert looks_like_address("200 E Las Olas Blvd")
    assert not looks_like_address("Las Olas Blvd")
    assert address_text("200 E Las Olas Blvd") == "200 E Las Olas Blvd, FL"
    assert address_text("200 E Las Olas Blvd, Fort Lauderdale, Florida").endswith("Florida")
    assert address_text("Las Olas & 3rd Ave", "Fort Lauderdale") == (
        "Las Olas & 3rd Ave, Fort Lauderdale, FL"
    )
    assert address_text("1 Las Olas, Fort Lauderdale", "Fort Lauderdale").endswith(
        "Fort Lauderdale, FL"
    )


def test_street_rank_puts_main_streets_before_ramps() -> None:
    names = ["MIC TO SB NW 42 AVE", "NW 42 AVE TO87200131", "LEJEUNE RD/NW 42 AVE"]
    ranked = sorted(names, key=lambda name: street_rank(name, "NW 42 AVE"))
    assert ranked[0] == "LEJEUNE RD/NW 42 AVE"
    assert street_text("NW 42nd Avenue") == "NW 42 AVE"


def test_parse_intersection_separators() -> None:
    assert parse_intersection("Las Olas & 3rd Ave") == ("Las Olas", "3rd Ave")
    assert parse_intersection("E Las Olas Blvd y SE 3rd Ave") == ("E Las Olas Blvd", "SE 3rd Ave")
    assert parse_intersection("Broward Blvd at Andrews Ave") == ("Broward Blvd", "Andrews Ave")
    assert parse_intersection("Las Olas Blvd") is None
    assert parse_intersection("Las Olas & 3") is None


def test_tiger_where_accepts_ordinals_but_only_at_a_word_start() -> None:
    where = tiger_where("SE 3rd Ave") or ""
    assert "LIKE 'SE 3% AVE%'" in where and "LIKE '% SE 3% AVE%'" in where
    assert "'%SE 3" not in where  # "SE 13TH AVE" no debe coincidir


def test_name_where_doubles_quotes() -> None:
    assert name_where("COUNTY", "St. Johns") == "COUNTY = 'St. Johns'"
    assert name_where("NAME", "O'Brien") == "NAME = 'O''Brien'"
