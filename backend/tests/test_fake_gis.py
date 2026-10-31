"""El backend completo contra el GIS falso: el falso imita lo que el cliente GIS espera.

Si una de estas pruebas falla tras cambiar el cliente GIS, el falso dejó de parecerse a FDOT,
FDACS o al Censo y el E2E del mapa no sería confiable (ADR-10 del frontend).
"""

from dataclasses import replace

import httpx
import pytest

from app.api.deps import build_services
from app.main import create_app
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.map import MapService
from tests.conftest import make_settings
from tests.fake_gis import create_fake_gis
from tests.fake_gis_data import END, ROADWAY, START

FAKE = "http://fake-gis"


@pytest.fixture
async def stack():
    fake = create_fake_gis()
    settings = make_settings(
        gis_fdot_base_url=f"{FAKE}/arcgis/rest/services",
        gis_fdacs_parcels_url=f"{FAKE}/fdacs/parcels/0",
        gis_census_geocoder_url=f"{FAKE}/census/onelineaddress",
        gis_miami_dade_parcels_url=f"{FAKE}/miami-dade/parcels/26",
        gis_tiger_roads_url=f"{FAKE}/tiger/Transportation/MapServer",
    )
    gis_http = httpx.AsyncClient(transport=httpx.ASGITransport(app=fake))
    cache = TtlCache(settings.gis_cache_ttl_seconds)
    maps = MapService(settings, GisClient(settings, gis_http), cache)
    app = create_app(settings, replace(build_services(settings), maps=maps), frontend_dist=None)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        yield client, fake.state.calls
    await gis_http.aclose()


async def test_point_on_the_control_case(stack) -> None:
    client, calls = stack
    body = (await client.get("/api/map/point", params={"lat": START[0], "lon": START[1]})).json()
    road = body["roads"][0]
    assert (road["roadway_id"], road["route"], road["section"]) == (ROADWAY, "SR 953", "281")
    assert (road["kind"], road["milepost"], road["local_name"]) == (
        "state",
        3.124,
        "LEJEUNE RD/NW 42 AVE",
    )
    assert body["location"]["county"] == "Miami-Dade" and body["location"]["zip"] == "33126"
    assert body["jurisdiction"]["authority"] == "FDOT"
    assert body["parcel"] is None and "PARCEL_IS_ROAD" in body["warnings"]
    assert {source["status"] for source in body["sources"]} == {"ok"}
    assert len(calls) == 8 and not any(call["authorization"] for call in calls)


async def test_point_off_the_road_keeps_location_and_parcel(stack) -> None:
    client, _ = stack
    params = {"lat": START[0], "lon": START[1] + 0.003}
    body = (await client.get("/api/map/point", params=params)).json()
    assert body["roads"] == [] and "NO_ROAD_NEARBY" in body["warnings"]
    assert body["parcel"]["owner_name"] == "PROPIETARIO SINTETICO 1"
    assert body["location"]["city"] == "Miami"


async def test_segment_on_the_control_case(stack) -> None:
    client, _ = stack
    params = {"start_lat": END[0], "start_lon": END[1], "end_lat": START[0], "end_lon": START[1]}
    body = (await client.get("/api/map/segment", params=params)).json()
    assert body["osp_row"] == {
        "county": "Miami-Dade",
        "state_road_id": "SR 953",
        "section_number": "281",
        "beginning_milepost": 3.124,
        "ending_milepost": 3.839,
    }
    assert body["geometry"]["coordinates"][0] == [START[1], START[0]]


async def test_search_through_the_fake(stack) -> None:
    client, _ = stack
    route = (await client.get("/api/map/search", params={"q": "SR 953 3.5"})).json()
    assert route["results"][0]["label"] == "SR 953 · MP 3.500"
    assert route["results"][0]["roadway_id"] == ROADWAY
    street = (await client.get("/api/map/search", params={"q": "NW 42nd Avenue"})).json()
    assert [result["label"] for result in street["results"]] == ["LEJEUNE RD/NW 42 AVE"]
    address = (await client.get("/api/map/search", params={"q": "1000 NW 42nd Ave"})).json()
    assert address["results"][0]["kind"] == "address"
    assert {source["status"] for source in address["sources"]} == {"ok"}


async def test_trace_on_the_control_case_gives_the_osp_row(stack) -> None:
    client, _ = stack
    # Dibujado con un vértice intermedio y a unos metros de la línea central, como a mano.
    path = f"{START[0]},{START[1]};25.776800,-80.263760;{END[0]},{END[1]}"
    body = (await client.get("/api/map/trace", params={"path": path})).json()
    assert [row["state_road_id"] for row in body["rows"]] == ["SR 953"]
    row = body["rows"][0]
    assert (row["county"], row["roadway_id"], row["section_number"]) == (
        "Miami-Dade",
        ROADWAY,
        "281",
    )
    assert (row["beginning_milepost"], row["ending_milepost"]) == (3.124, 3.839)
    assert (row["on_turnpike"], row["kind"]) == (False, "state")
    assert row["local_name"] == "LEJEUNE RD/NW 42 AVE"
    assert row["geometry"]["coordinates"][0] == [START[1], START[0]]
    assert body["warnings"] == [] and {s["status"] for s in body["sources"]} == {"ok"}


async def test_parcel_outlines_come_from_the_county_without_owners(stack) -> None:
    client, _ = stack
    box = {"west": -80.2650, "south": 25.7710, "east": -80.2600, "north": 25.7750}
    body = (await client.get("/api/map/parcels", params=box)).json()
    assert body["source"] == "miami_dade_parcels" and body["truncated"] is False
    assert [parcel["parcel_id"] for parcel in body["parcels"]][:2] == [
        "300000000000",
        "300000000001",
    ]
    assert set(body["parcels"][0]) == {"parcel_id", "rings"}


async def test_area_lists_only_the_municipalities_inside_the_county(stack) -> None:
    client, _ = stack
    assert [c["name"] for c in (await client.get("/api/map/counties")).json()] == ["Miami-Dade"]
    county = (await client.get("/api/map/area", params={"county": "miami-dade"})).json()
    assert county["county"] == "Miami-Dade" and county["city"] is None
    assert [city["name"] for city in county["cities"]] == ["Miami"]
    assert county["bounds"] == {"west": -80.3, "south": 25.74, "east": -80.22, "north": 25.81}
    city = await client.get("/api/map/area", params={"county": "Miami-Dade", "city": "miami"})
    assert city.json()["city"] == "Miami" and city.json()["bounds"]["west"] == -80.28
    for params in ({"county": "Nowhere"}, {"county": "Miami-Dade", "city": "Zona Sintetica"}):
        missing = await client.get("/api/map/area", params=params)
        assert missing.status_code == 404
        assert missing.json()["detail"]["code"] == "MAP_AREA_NOT_FOUND"


async def test_crossing_in_a_city_gives_the_fdot_milepost_once(stack) -> None:
    client, _ = stack
    params = {"q": "NW 42nd Ave & W Flagler St", "county": "Miami-Dade", "city": "Miami"}
    body = (await client.get("/api/map/search", params=params)).json()
    assert len(body["results"]) == 1  # FDOT, Censo y TIGER ven el mismo cruce
    result = body["results"][0]
    assert (result["kind"], result["roadway_id"], result["milepost"]) == (
        "intersection",
        ROADWAY,
        3.124,
    )
    statuses = {source["id"]: source["status"] for source in body["sources"]}
    assert statuses == {"fdot_crossings": "ok", "census_geocoder": "ok", "tiger_crossings": "ok"}


async def test_streets_that_never_cross_give_the_nearest_point(stack) -> None:
    client, _ = stack
    params = {"q": "NW 41st Ave & NW 42nd Ave", "county": "Miami-Dade", "city": "Miami"}
    result = (await client.get("/api/map/search", params=params)).json()["results"][0]
    assert result["kind"] == "nearest" and 95 < result["distance_m"] < 105
    assert "No se cruzan" in result["detail"]


async def test_a_city_adds_local_streets_from_the_census(stack) -> None:
    client, _ = stack
    params = {"q": "Flagler", "county": "Miami-Dade", "city": "Miami"}
    body = (await client.get("/api/map/search", params=params)).json()
    assert [(r["kind"], r["label"]) for r in body["results"]] == [("street", "W Flagler St")]
    without_city = (await client.get("/api/map/search", params={"q": "Flagler"})).json()
    assert without_city["results"] == []  # sin zona sólo se busca en vías del FDOT
