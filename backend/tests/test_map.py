import httpx
import respx

GIS = "https://gis.test/arcgis/rest/services"


def _feature(attributes: dict, paths: list | None = None) -> dict:
    value = {"attributes": attributes}
    if paths is not None:
        value["geometry"] = {"paths": paths}
    return value


def _routes(
    router: respx.MockRouter,
    *,
    lrs: bool = True,
    failing: bool = False,
    names: list[dict] | None = None,
) -> None:
    responses = {
        "/RCI_Layers/MapServer/8/query": [
            _feature(
                {
                    "ROADWAY": "87281000",
                    "COUNTY": "87",
                    "SECTION": "281",
                    "BEGIN_POST": 3.124,
                    "END_POST": 3.839,
                },
                [[[-80.26361, 25.771778, 3.124], [-80.264005, 25.782147, 3.839]]],
            )
        ]
        if lrs
        else [],
        "/RCI_Layers/MapServer/15/query": [_feature({"ROADWAY": "87281000", "ROUTE": "SR  953"})],
        "/RCI_Layers/MapServer/2/query": [],
        "/RCI_Layers/MapServer/13/query": names
        or [_feature({"ROADWAY": "87281000", "NAME": "LEJEUNE RD"})],
        "/Admin_Boundaries/MapServer/6/query": [
            _feature({"COUNTY": "Miami-Dade", "CNTYNO": "87", "DISTRICT": "6"})
        ],
        "/Admin_Boundaries/MapServer/7/query": [_feature({"NAME": "Miami"})],
        "/Admin_Boundaries/MapServer/8/query": [_feature({"ZIP": "33126"})],
    }
    for path, features in responses.items():
        router.get(f"{GIS}{path}").respond(500 if failing else 200, json={"features": features})
    router.get("https://parcels.test/0/query").respond(
        500 if failing else 200,
        json={
            "features": [
                _feature(
                    {
                        "CO_NO": 13.0,
                        "PARCEL_ID": "synthetic-1",
                        "DOR_UC": "087",
                        "OWN_NAME": "OWNER SYNTHETIC",
                    }
                )
            ]
        },
    )


async def test_point_maps_control_case_and_never_sends_authorization(client, smartsheet) -> None:
    _routes(smartsheet)
    response = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    assert response.status_code == 200
    body = response.json()
    assert body["roads"][0]["roadway_id"] == "87281000"
    assert body["roads"][0]["milepost"] == 3.124
    calls = [call.request for call in smartsheet.calls if str(call.request.url).startswith(GIS)]
    assert calls and all("Authorization" not in call.headers for call in calls)


async def test_segment_returns_ordered_mileposts_and_osp_row(client, smartsheet) -> None:
    _routes(smartsheet)
    response = await client.get(
        "/api/map/segment",
        params={
            "start_lat": 25.771778,
            "start_lon": -80.26361,
            "end_lat": 25.782147,
            "end_lon": -80.264005,
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert (body["begin_milepost"], body["end_milepost"]) == (3.124, 3.839)
    assert body["osp_row"]["section_number"] == "281"


async def test_source_failure_is_partial_and_refresh_bypasses_cache(client, smartsheet) -> None:
    _routes(smartsheet)
    first = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    calls = len(smartsheet.calls)
    await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    assert len(smartsheet.calls) == calls
    refreshed = await client.get(
        "/api/map/point", params={"lat": 25.771778, "lon": -80.26361, "refresh": True}
    )
    assert first.status_code == refreshed.status_code == 200 and len(smartsheet.calls) > calls


async def test_outside_florida_never_queries_gis(client, smartsheet) -> None:
    response = await client.get("/api/map/point", params={"lat": 40, "lon": -80})
    assert response.json()["detail"]["code"] == "COORDINATES_OUT_OF_FLORIDA"
    assert [call for call in smartsheet.calls if "gis.test" in str(call.request.url)] == []


async def test_all_gis_sources_down_returns_safe_error(client, smartsheet) -> None:
    _routes(smartsheet, failing=True)
    response = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "GIS_UNAVAILABLE"


async def test_gis_disabled(make_client, smartsheet) -> None:
    client = make_client(app_gis_enabled=False)
    disabled = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    assert disabled.status_code == 503
    assert disabled.json()["detail"]["code"] == "GIS_DISABLED"


async def test_only_line_layers_send_a_search_radius(client, smartsheet) -> None:
    """FDOT y FDACS devuelven vacío en polígonos si reciben `distance=0` (verificado 2026-10-30)."""
    _routes(smartsheet)
    response = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    sent = {
        call.request.url.path: dict(call.request.url.params)
        for call in smartsheet.calls
        if call.request.url.host in {"gis.test", "parcels.test"}
    }
    assert float(sent["/arcgis/rest/services/RCI_Layers/MapServer/13/query"]["distance"]) == 25
    for polygon in ("Admin_Boundaries/MapServer/6", "Admin_Boundaries/MapServer/8"):
        assert "distance" not in sent[f"/arcgis/rest/services/{polygon}/query"]
    assert "distance" not in sent["/0/query"]
    assert response.json()["location"]["county"] == "Miami-Dade"


async def test_local_name_is_the_one_whose_range_contains_the_milepost(client, smartsheet) -> None:
    names = [
        _feature(
            {"ROADWAY": "87281000", "NAME": "NW 42 AVE", "BEGIN_POST": 3.117, "END_POST": 5.8}
        ),
        _feature({"ROADWAY": "87281000", "NAME": "SW 42 AVE", "BEGIN_POST": 0, "END_POST": 3.117}),
    ]
    _routes(smartsheet, names=names)
    response = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    assert response.json()["roads"][0]["local_name"] == "NW 42 AVE"


async def test_search_route_and_milepost_returns_the_point_on_the_route(client, smartsheet) -> None:
    state = _feature(
        {
            "ROADWAY": "87281000",
            "ROUTE": "SR  953",
            "COUNTY": "Miami-Dade",
            "BEGIN_POST": 0,
            "END_POST": 11.735,
        }
    )
    lrs = _feature(
        {"ROADWAY": "87281000"}, [[[-80.26361, 25.771778, 3.124], [-80.264005, 25.782147, 3.839]]]
    )
    smartsheet.get(f"{GIS}/RCI_Layers/MapServer/15/query").respond(json={"features": [state]})
    smartsheet.get(f"{GIS}/RCI_Layers/MapServer/8/query").respond(json={"features": [lrs]})
    response = await client.get("/api/map/search", params={"q": "SR 953 MP 3.5"})
    result = response.json()["results"][0]
    assert (result["kind"], result["label"]) == ("milepost", "SR 953 · MP 3.500")
    assert result["roadway_id"] == "87281000" and 25.771778 < result["lat"] < 25.782147
    wheres = [
        call.request.url.params["where"]
        for call in smartsheet.calls
        if call.request.url.host == "gis.test"
    ]
    assert wheres == ["ROUTENUM = '953'", "ROADWAY IN ('87281000')"]


async def test_search_street_normalizes_the_text_and_uses_the_middle_point(
    client, smartsheet
) -> None:
    street = _feature(
        {
            "ROADWAY": "87281000",
            "NAME": "LEJEUNE RD/NW 42 AVE",
            "COUNTY": "Miami-Dade",
            "BEGIN_POST": 3.117,
            "END_POST": 5.822,
        },
        [[[-80.2636, 25.77], [-80.264, 25.79], [-80.2645, 25.8]]],
    )
    route = smartsheet.get(f"{GIS}/RCI_Layers/MapServer/13/query").respond(
        json={"features": [street]}
    )
    body = (await client.get("/api/map/search", params={"q": "NW 42nd Avenue"})).json()
    assert route.calls.last.request.url.params["where"] == (
        "(UPPER(NAME) LIKE 'NW 42 AVE%' OR UPPER(NAME) LIKE '% NW 42 AVE%' "
        "OR UPPER(NAME) LIKE '%/NW 42 AVE%')"
    )
    result = body["results"][0]
    assert (result["kind"], result["lat"], result["lon"]) == ("street", 25.79, -80.264)
    assert result["detail"] == "Miami-Dade · vía 87281000 · MP 3.117 a 5.822"


async def test_search_address_survives_a_failed_street_source(client, smartsheet) -> None:
    match = {
        "matchedAddress": "200 E LAS OLAS BLVD, FORT LAUDERDALE, FL, 33301",
        "coordinates": {"x": -80.141826, "y": 26.119041},
    }
    geocoder = smartsheet.get("https://geocoder.test/onelineaddress").respond(
        json={"result": {"addressMatches": [match]}}
    )
    smartsheet.get(f"{GIS}/RCI_Layers/MapServer/13/query").respond(500)
    body = (await client.get("/api/map/search", params={"q": "200 E Las Olas Blvd"})).json()
    assert [result["kind"] for result in body["results"]] == ["address"]
    statuses = {source["id"]: source["status"] for source in body["sources"]}
    assert statuses == {"census_geocoder": "ok", "fdot_streets": "error"}
    assert geocoder.calls.last.request.url.params["address"] == "200 E Las Olas Blvd, FL"


async def test_crossing_cut_by_fdot_is_found_without_its_street_type(client, smartsheet) -> None:
    """FDOT recorta INTSEC_ROA a 20 caracteres: "US-1/SR-5/FEDERAL HW" (PEN-39)."""
    smartsheet.get("https://geocoder.test/onelineaddress").respond(
        json={"result": {"addressMatches": []}}
    )
    smartsheet.get(f"{GIS}/RCI_Layers/MapServer/13/query").respond(
        json={"features": [_feature({"ROADWAY": "86090000", "NAME": "SUNRISE BLVD"})]}
    )
    crossing = {
        "attributes": {
            "ROADWAY": "86090000",
            "INTSEC_ROA": "US-1/SR-5/FEDERAL HW",
            "BEGIN_POST": 1.975,
            "COUNTY": "Broward",
        },
        "geometry": {"x": -80.1372, "y": 26.1377},
    }

    def intersections(request):
        where = request.url.params["where"]
        found = "'%/FEDERAL%'" in where and "FEDERAL HWY" not in where
        return httpx.Response(200, json={"features": [crossing] if found else []})

    layer = smartsheet.get(f"{GIS}/RCI_Layers/MapServer/6/query").mock(side_effect=intersections)
    body = (await client.get("/api/map/search", params={"q": "Federal Hwy & Sunrise"})).json()
    assert [(r["kind"], r["milepost"]) for r in body["results"]] == [("intersection", 1.975)]
    assert body["results"][0]["label"] == "SUNRISE BLVD y US-1/SR-5/FEDERAL HW"
    assert layer.call_count == 3  # Sunrise una vez; "Federal Hwy" completo y luego sin "HWY"


async def test_search_coordinates_answers_without_calling_gis(client, smartsheet) -> None:
    body = (await client.get("/api/map/search", params={"q": "25.771778, -80.263610"})).json()
    assert body["results"][0]["kind"] == "coordinates"
    assert not any(call.request.url.host == "gis.test" for call in smartsheet.calls)


async def test_parcel_county_code_is_an_integer_code(client, smartsheet) -> None:
    _routes(smartsheet)
    response = await client.get("/api/map/point", params={"lat": 25.771778, "lon": -80.26361})
    assert response.json()["parcel"]["county_code_dor"] == "13"


async def test_firewall_html_is_a_failed_source_and_the_host_rests(client, smartsheet) -> None:
    """El Censo responde 200 con HTML "Request Rejected" al bloquear la IP (2026-10-31)."""
    rejected = smartsheet.get("https://geocoder.test/onelineaddress").respond(
        200,
        text="<html><title>Request Rejected</title></html>",
        headers={"Content-Type": "text/html"},
    )
    smartsheet.get(f"{GIS}/RCI_Layers/MapServer/13/query").respond(json={"features": []})
    for _ in range(2):
        params = {"q": "NW 42 Ave & W Flagler St", "refresh": True}
        response = await client.get("/api/map/search", params=params)
        assert response.status_code == 200
        statuses = {source["id"]: source["status"] for source in response.json()["sources"]}
        assert statuses == {"fdot_crossings": "ok", "census_geocoder": "error"}
    assert rejected.call_count == 1  # tras el rechazo, el servidor se salta un rato
