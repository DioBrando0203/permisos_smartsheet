"""Trazo (PEN-32): validación, Turnpike y fuentes caídas, con el GIS simulado por `respx`."""

import pytest
import respx

GIS = "https://gis.test/arcgis/rest/services"
CONTROL = "25.771778,-80.263610;25.782147,-80.264005"
LRS = {
    "attributes": {"ROADWAY": "87281000", "COUNTY": "87", "SECTION": "281"},
    "geometry": {"paths": [[[-80.26361, 25.771778, 3.124], [-80.264005, 25.782147, 3.839]]]},
}


def _routes(router: respx.MockRouter, *, lrs: list | None = None, districts: list | None = None):
    responses = {
        "/RCI_Layers/MapServer/8/query": [LRS] if lrs is None else lrs,
        "/RCI_Layers/MapServer/15/query": [
            {"attributes": {"ROADWAY": "87281000", "ROUTE": "SR  953"}}
        ],
        "/RCI_Layers/MapServer/2/query": [],
        "/RCI_Layers/MapServer/13/query": [],
        "/Admin_Boundaries/MapServer/6/query": [
            {"attributes": {"COUNTY": "Miami-Dade", "CNTYNO": "87"}}
        ],
        "/Admin_Boundaries/MapServer/13/query": districts or [{"attributes": {"DVALUE": "D6"}}],
    }
    for path, features in responses.items():
        router.get(f"{GIS}{path}", name=path).respond(json={"features": features})


async def test_turnpike_district_marks_the_row(client, smartsheet) -> None:
    _routes(
        smartsheet, districts=[{"attributes": {"DVALUE": "D6"}}, {"attributes": {"DVALUE": "D8"}}]
    )
    body = (await client.get("/api/map/trace", params={"path": CONTROL})).json()
    assert body["rows"][0]["on_turnpike"] is True
    assert body["rows"][0]["state_road_id"] == "SR 953"
    assert body["length_mi"] == body["rows"][0]["length_mi"]
    assert body["input_length_mi"] == pytest.approx(body["length_mi"], abs=0.002)
    assert body["adjustment"] == {"start_m": 0.0, "end_m": 0.0}


async def test_trace_reports_how_far_fdot_adjusted_its_endpoints(client, smartsheet) -> None:
    _routes(smartsheet)
    path = "25.771778,-80.263550;25.782147,-80.263945"
    body = (await client.get("/api/map/trace", params={"path": path})).json()
    assert body["rows"][0]["state_road_id"] == "SR 953"
    assert body["adjustment"]["start_m"] == pytest.approx(6, abs=1)
    assert body["adjustment"]["end_m"] == pytest.approx(6, abs=1)
    assert body["matched_percent"] == 100
    assert body["unmatched_length_mi"] == 0


async def test_trace_warns_if_the_drawn_line_leaves_and_rejoins_the_road(
    client, smartsheet
) -> None:
    _routes(smartsheet)
    path = (
        "25.771778,-80.263610;25.775,-80.26375;25.777,-80.261;25.779,-80.2639;25.782147,-80.264005"
    )
    body = (await client.get("/api/map/trace", params={"path": path})).json()
    assert len(body["rows"]) == 2
    assert "TRACE_PARTIAL" in body["warnings"]
    assert 0 < body["matched_percent"] < 100
    assert body["unmatched_length_mi"] > 0.1


async def test_incomplete_geometry_has_unknown_length_and_a_warning(client, smartsheet) -> None:
    split = {
        **LRS,
        "geometry": {
            "paths": [
                [[-80.26361, 25.771778, 3.124], [-80.2638, 25.777, 3.48]],
                [[-80.2638, 25.7771, 3.49], [-80.264005, 25.782147, 3.839]],
            ]
        },
    }
    _routes(smartsheet, lrs=[split])
    body = (await client.get("/api/map/trace", params={"path": CONTROL})).json()
    assert body["length_mi"] is None
    assert body["rows"][0]["length_mi"] is None
    assert "TRACE_GEOMETRY_INCOMPLETE" in body["warnings"]


async def test_refresh_trace_queries_gis_again(client, smartsheet) -> None:
    _routes(smartsheet)
    route = smartsheet.routes["/RCI_Layers/MapServer/8/query"]
    await client.get("/api/map/trace", params={"path": CONTROL})
    before = route.call_count
    await client.get("/api/map/trace", params={"path": CONTROL})
    assert route.call_count == before
    await client.get("/api/map/trace", params={"path": CONTROL, "refresh": "true"})
    assert route.call_count > before


@pytest.mark.parametrize(
    ("path", "code"),
    [
        ("25.771778,-80.263610", "TRACE_INVALID"),
        ("25.771778,-80.263610;calle", "TRACE_INVALID"),
        ("40.0,-80.0;40.1,-80.0", "COORDINATES_OUT_OF_FLORIDA"),
        ("25.0,-80.3;25.5,-80.3", "SEGMENT_TOO_LONG"),
    ],
)
async def test_invalid_traces_never_query_gis(client, smartsheet, path, code) -> None:
    response = await client.get("/api/map/trace", params={"path": path})
    assert response.status_code == 422 and response.json()["detail"]["code"] == code
    assert [call for call in smartsheet.calls if "gis.test" in str(call.request.url)] == []


async def test_a_trace_away_from_roads_answers_with_a_warning(client, smartsheet) -> None:
    _routes(smartsheet, lrs=[])
    body = (await client.get("/api/map/trace", params={"path": CONTROL})).json()
    assert body["rows"] == [] and "NO_ROAD_NEARBY" in body["warnings"]


async def test_lrs_down_is_a_gis_error(client, smartsheet) -> None:
    smartsheet.get(f"{GIS}/RCI_Layers/MapServer/8/query").respond(500)
    response = await client.get("/api/map/trace", params={"path": CONTROL})
    assert response.status_code == 502 and response.json()["detail"]["code"] == "GIS_UNAVAILABLE"
