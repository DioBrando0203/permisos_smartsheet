"""Una fuente que no conecta no frena el punto y, en Broward, la parcela sale del condado.

PEN-30: con FDACS caído, cada punto tardaba 60 s (tres intentos de 20 s) y llegaba sin parcela.
"""

import httpx
import respx

GIS = "https://gis.test/arcgis/rest/services"
FDACS = "https://parcels.test/0/query"
BROWARD = "https://broward.test/0/query"
POINT = {"lat": 26.138, "lon": -80.1095}
BROWARD_COUNTY = {"COUNTY": "Broward", "CNTYNO": "86", "DISTRICT": "4"}


def _feature(attributes: dict) -> dict:
    return {"attributes": attributes}


def _fdot(router: respx.MockRouter, county: dict) -> None:
    """FDOT sin vías cerca y con el condado pedido: sólo importan límites y parcelas."""
    for layer in (8, 15, 2, 13):
        router.get(f"{GIS}/RCI_Layers/MapServer/{layer}/query").respond(json={"features": []})
    for layer, attributes in {
        6: county,
        7: {"NAME": "Fort Lauderdale"},
        8: {"ZIP": "33304"},
    }.items():
        router.get(f"{GIS}/Admin_Boundaries/MapServer/{layer}/query").respond(
            json={"features": [_feature(attributes)]}
        )


async def test_unreachable_fdacs_is_not_retried_and_broward_gives_the_folio(
    make_client, smartsheet
) -> None:
    client = make_client(gis_max_retries=2)
    _fdot(smartsheet, BROWARD_COUNTY)
    fdacs = smartsheet.get(FDACS).mock(side_effect=httpx.ConnectTimeout("sin conexión"))
    broward = smartsheet.get(BROWARD).respond(
        json={"features": [_feature({"FOLIO": "000000000002"})]}
    )
    body = (await client.get("/api/map/point", params=POINT)).json()
    assert fdacs.call_count == 1
    statuses = {source["id"]: source["status"] for source in body["sources"]}
    assert (statuses["fdacs_parcels"], statuses["broward_parcels"]) == ("timeout", "ok")
    assert body["parcel"] == {
        "parcel_id": "000000000002",
        "county_code_dor": "16",
        "use_code": None,
        "use_label": None,
        "public_owner": None,
        "owner_name": None,
        "source": "broward_parcels",
    }
    assert "SOURCE_FAILED" in body["warnings"]
    assert "distance" not in broward.calls.last.request.url.params
    # Otro punto, mientras dura la pausa: FDACS no se vuelve a intentar.
    other = {"lat": POINT["lat"] + 0.001, "lon": POINT["lon"]}
    again = (await client.get("/api/map/point", params=other)).json()
    assert fdacs.call_count == 1
    assert {s["id"]: s["status"] for s in again["sources"]}["fdacs_parcels"] == "timeout"
    assert again["parcel"]["source"] == "broward_parcels"


async def test_unreachable_host_is_tried_again_after_the_pause(make_client, smartsheet) -> None:
    client = make_client(gis_unreachable_cooldown_seconds=0)
    _fdot(smartsheet, BROWARD_COUNTY)
    fdacs = smartsheet.get(FDACS).mock(side_effect=httpx.ConnectError("rechazada"))
    smartsheet.get(BROWARD).respond(json={"features": []})
    for lat in (POINT["lat"], POINT["lat"] + 0.001):
        body = (await client.get("/api/map/point", params={"lat": lat, "lon": POINT["lon"]})).json()
        assert {s["id"]: s["status"] for s in body["sources"]}["fdacs_parcels"] == "error"
    assert fdacs.call_count == 2


async def test_fdacs_failure_outside_broward_has_no_fallback(client, smartsheet) -> None:
    _fdot(smartsheet, {"COUNTY": "Miami-Dade", "CNTYNO": "87", "DISTRICT": "6"})
    smartsheet.get(FDACS).respond(500)
    broward = smartsheet.get(BROWARD).respond(json={"features": []})
    body = (await client.get("/api/map/point", params=POINT)).json()
    assert body["parcel"] is None and not broward.called
    assert "broward_parcels" not in {source["id"] for source in body["sources"]}


async def test_fdacs_answer_in_broward_needs_no_fallback(client, smartsheet) -> None:
    _fdot(smartsheet, BROWARD_COUNTY)
    smartsheet.get(FDACS).respond(
        json={"features": [_feature({"CO_NO": 16.0, "PARCEL_ID": "000000000003"})]}
    )
    broward = smartsheet.get(BROWARD).respond(json={"features": []})
    body = (await client.get("/api/map/point", params=POINT)).json()
    assert body["parcel"]["source"] == "fdacs_parcels" and not broward.called
