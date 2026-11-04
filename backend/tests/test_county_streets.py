"""Calles del condado por celda y por trazo (PEN-41, SPEC-B14 CA-33 y CA-35)."""

STJOHNS = "https://stjohns.test/36/query"
CELL = {"west": -81.48, "south": 30.08, "east": -81.46, "north": 30.10}
TRACE = "30.085,-81.475;30.085,-81.470"


def _segment(oid: int, name: str, maintainer: str, lat: float = 30.085) -> dict:
    attributes = {"OBJECTID": oid, "NAME": name, "MAINTENANCE": maintainer, "GATED": "N"}
    return {"attributes": attributes, "geometry": {"paths": [[[-81.476, lat], [-81.469, lat]]]}}


async def test_cell_in_st_johns_gives_streets_with_their_authority(client, smartsheet) -> None:
    route = smartsheet.get(STJOHNS).respond(
        json={
            "features": [
                _segment(1, "County Road 210 W", "St Johns County"),
                _segment(2, "Future Ln", "Proposed"),
                _segment(3, "Far Rd", "Out of County"),
            ]
        }
    )
    body = (await client.get("/api/map/streets", params=CELL)).json()
    assert (body["source"], body["county"], body["truncated"]) == (
        "stjohns_roads",
        "St. Johns",
        False,
    )
    assert [(s["id"], s["authority"], s["authority_name"]) for s in body["streets"]] == [
        ("1", "COUNTY", "St. Johns County"),
        ("2", None, None),
    ]
    assert body["streets"][0]["paths"] == [[[-81.476, 30.085], [-81.469, 30.085]]]
    params = route.calls.last.request.url.params
    assert params["geometryType"] == "esriGeometryEnvelope" and "maxAllowableOffset" in params
    assert "Authorization" not in route.calls.last.request.headers


async def test_cell_outside_every_adapter_is_not_asked(client, smartsheet) -> None:
    route = smartsheet.get(STJOHNS).respond(json={"features": []})
    cell = {"west": -80.27, "south": 25.76, "east": -80.25, "north": 25.78}
    body = (await client.get("/api/map/streets", params=cell)).json()
    assert body == {"source": None, "county": None, "streets": [], "truncated": False}
    assert not route.called


async def test_invalid_cell_and_source_down(client, smartsheet) -> None:
    big = {**CELL, "east": -81.45}
    assert (await client.get("/api/map/streets", params=big)).json()["detail"]["code"] == (
        "STREET_CELL_INVALID"
    )
    smartsheet.get(STJOHNS).respond(500)
    response = await client.get("/api/map/streets", params=CELL)
    assert (response.status_code, response.json()["detail"]["code"]) == (502, "GIS_UNAVAILABLE")


async def test_trace_gives_the_county_streets_it_follows(client, smartsheet) -> None:
    smartsheet.get(STJOHNS).respond(
        json={"features": [_segment(1, "County Road 210 W", "St Johns County")]}
    )
    response = await client.get("/api/map/trace/streets", params={"path": TRACE})
    body = response.json()
    assert (body["county"], body["source"], body["warnings"]) == ("St. Johns", "stjohns_roads", [])
    [row] = body["streets"]
    assert (row["name"], row["authority"], row["maintainer"]) == (
        "County Road 210 W",
        "COUNTY",
        "St Johns County",
    )
    assert 0.29 < row["length_mi"] < 0.31
    assert {source["id"]: source["status"] for source in body["sources"]} == {"stjohns_roads": "ok"}


async def test_trace_outside_st_johns_and_with_the_source_down(client, smartsheet) -> None:
    route = smartsheet.get(STJOHNS).respond(500)
    miami = "25.771778,-80.263610;25.782147,-80.264005"
    body = (await client.get("/api/map/trace/streets", params={"path": miami})).json()
    assert (body["county"], body["streets"], body["warnings"]) == (None, [], ["NO_COUNTY_SOURCE"])
    assert not route.called
    response = await client.get("/api/map/trace/streets", params={"path": TRACE})
    assert (response.status_code, response.json()["detail"]["code"]) == (502, "GIS_UNAVAILABLE")
    bad = await client.get("/api/map/trace/streets", params={"path": "30.085,-81.475"})
    assert bad.json()["detail"]["code"] == "TRACE_INVALID"
