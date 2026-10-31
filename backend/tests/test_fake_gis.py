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
        "state_road_id": ROADWAY,
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
