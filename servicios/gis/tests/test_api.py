from fastapi.testclient import TestClient

from app.main import create_app


def test_sources_and_validation_without_smartsheet() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/map/sources")
        invalid = client.get("/api/map/point", params={"lat": 100, "lon": 0})
    assert response.status_code == 200
    assert response.json()
    assert invalid.status_code == 422


def test_map_routes_are_exposed() -> None:
    paths = set(create_app().openapi()["paths"])
    assert {
        "/api/map/point",
        "/api/map/trace",
        "/api/map/search",
        "/api/map/parcels",
        "/api/map/streets",
        "/api/map/trace/streets",
        "/api/map/counties",
        "/api/map/area",
        "/api/map/segment",
        "/api/map/sources",
    } <= paths
