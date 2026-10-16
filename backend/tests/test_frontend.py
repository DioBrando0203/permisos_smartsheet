from pathlib import Path

import httpx

from app.api.deps import build_services
from app.main import create_app
from tests.conftest import make_settings


def make_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>panel</html>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (dist / "favicon.svg").write_text("<svg/>")
    (tmp_path / "secreto.txt").write_text("no")
    return dist


def client_for(dist: Path | None) -> httpx.AsyncClient:
    settings = make_settings()
    app = create_app(settings, build_services(settings), frontend_dist=dist)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost")


async def test_panel_routes_return_index(tmp_path: Path) -> None:
    async with client_for(make_dist(tmp_path)) as client:
        for path in ("/", "/hojas/1842596423880580", "/personas/ana%40example.com"):
            response = await client.get(path)
            assert response.status_code == 200 and response.text == "<html>panel</html>", path
        assert (await client.get("/assets/app.js")).text == "console.log(1)"
        assert (await client.get("/favicon.svg")).text == "<svg/>"


async def test_api_and_docs_are_not_hidden_by_the_panel(tmp_path: Path) -> None:
    async with client_for(make_dist(tmp_path)) as client:
        assert (await client.get("/api/health")).json()["status"] == "ok"
        assert (await client.get("/api/no-existe")).status_code == 404
        assert (await client.get("/docs")).status_code == 200
        assert (await client.get("/openapi.json")).status_code == 200


async def test_cannot_read_outside_dist(tmp_path: Path) -> None:
    async with client_for(make_dist(tmp_path)) as client:
        response = await client.get("/..%2Fsecreto.txt")
        assert response.text == "<html>panel</html>"


async def test_without_build_nothing_is_mounted(tmp_path: Path) -> None:
    async with client_for(tmp_path / "vacio") as client:
        assert (await client.get("/hojas/1")).status_code == 404
