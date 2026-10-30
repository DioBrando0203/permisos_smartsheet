import respx

GIS = "https://gis.test/arcgis/rest/services"


def _feature(attributes: dict, paths: list | None = None) -> dict:
    value = {"attributes": attributes}
    if paths is not None:
        value["geometry"] = {"paths": paths}
    return value


def _routes(router: respx.MockRouter, *, lrs: bool = True, failing: bool = False) -> None:
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
        "/RCI_Layers/MapServer/13/query": [_feature({"ROADWAY": "87281000", "NAME": "LEJEUNE RD"})],
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
                        "CO_NO": "13",
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
