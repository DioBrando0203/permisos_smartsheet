"""El punto consulta las calles del condado sólo en St. Johns (PEN-40, SPEC-B14 CA-32)."""

import respx

GIS = "https://gis.test/arcgis/rest/services"
STJOHNS = "https://stjohns.test/36/query"
POINT = {"lat": 29.892, "lon": -81.314}
ST_JOHNS = {"COUNTY": "St. Johns", "CNTYNO": "78", "DISTRICT": "2"}


def _feature(attributes: dict) -> dict:
    return {"attributes": attributes}


def _fdot(router: respx.MockRouter, county: dict, city: dict) -> None:
    """FDOT sin vías cerca: la jurisdicción depende del condado y de la ciudad."""
    for layer in (8, 15, 2, 13):
        router.get(f"{GIS}/RCI_Layers/MapServer/{layer}/query").respond(json={"features": []})
    for layer, attributes in {6: county, 7: city, 8: {"ZIP": "32084"}}.items():
        router.get(f"{GIS}/Admin_Boundaries/MapServer/{layer}/query").respond(
            json={"features": [_feature(attributes)]}
        )
    router.get("https://parcels.test/0/query").respond(json={"features": []})


def _street(name: str, maintainer: str) -> dict:
    lat = POINT["lat"] + 0.00003
    return {
        "attributes": {"NAME": name, "MAINTENANCE": maintainer, "GATED": "N"},
        "geometry": {"paths": [[[POINT["lon"] - 0.001, lat], [POINT["lon"] + 0.001, lat]]]},
    }


async def test_st_johns_point_uses_the_county_maintainer(client, smartsheet) -> None:
    _fdot(smartsheet, ST_JOHNS, {"NAME": "St. Augustine", "CLASSFP": "C1", "LSAD": "25"})
    county = smartsheet.get(STJOHNS).respond(
        json={"features": [_street("Synthetic St", "City of St Augustine")]}
    )
    body = (await client.get("/api/map/point", params=POINT)).json()
    assert body["jurisdiction"]["authority"] == "CITY"
    assert body["jurisdiction"]["name"] == "City of St. Augustine"
    assert body["jurisdiction"]["basis"] == "county_maintenance"
    assert {s["id"]: s["status"] for s in body["sources"]}["stjohns_roads"] == "ok"
    assert body["location"]["municipality_type"] == "city"
    request = county.calls.last.request
    assert request.url.params["returnGeometry"] == "true"
    assert request.url.params["distance"] == "25.0"
    assert "Authorization" not in request.headers


async def test_county_source_down_keeps_the_approximation(client, smartsheet) -> None:
    _fdot(smartsheet, ST_JOHNS, {"NAME": "Nocatee", "CLASSFP": "U2"})
    smartsheet.get(STJOHNS).respond(500)
    response = await client.get("/api/map/point", params=POINT)
    assert response.status_code == 200
    body = response.json()
    assert (body["location"]["city"], body["location"]["place"]) == (None, "Nocatee")
    assert body["jurisdiction"]["basis"] == "no_road"
    assert {s["id"]: s["status"] for s in body["sources"]}["stjohns_roads"] == "error"
    assert "SOURCE_FAILED" in body["warnings"]


async def test_outside_st_johns_the_county_layer_is_not_asked(client, smartsheet) -> None:
    _fdot(smartsheet, {"COUNTY": "Miami-Dade", "CNTYNO": "87"}, {"NAME": "Miami"})
    county = smartsheet.get(STJOHNS).respond(json={"features": []})
    body = (await client.get("/api/map/point", params=POINT)).json()
    assert not county.called
    assert "stjohns_roads" not in {source["id"] for source in body["sources"]}
