from collections.abc import AsyncIterator, Callable

import httpx
import pytest
import respx
from pydantic import SecretStr

from app.api.deps import build_services
from app.core.config import Settings
from app.main import create_app
from tests.factories import SHEET_ID, default_shares, me_json, page, sheet_json

BASE = "https://api.smartsheet.test/2.0"
FAKE_TOKEN = "token-de-prueba-123"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "smartsheet_access_token": SecretStr(FAKE_TOKEN),
        "smartsheet_base_url": BASE,
        "smartsheet_retry_base_seconds": 0.0,
        "smartsheet_max_retries": 2,
        "app_read_only": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def smartsheet() -> respx.MockRouter:
    """Smartsheet simulado; una solicitud sin ruta simulada hace fallar la prueba (QB-02)."""
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        router.get("/users/me").respond(json=me_json())
        router.get("/sheets").respond(json=page([sheet_json()]))
        router.get("/users/sheets").respond(json=page([]))
        router.get(f"/sheets/{SHEET_ID}").respond(json=sheet_json())
        router.get("/shares").respond(json={"items": default_shares()})
        router.get("/contacts").respond(json=page([]))
        router.get("/users").respond(json=page([]))
        router.get("/groups").respond(json=page([]))
        yield router


AppFactory = Callable[..., httpx.AsyncClient]


@pytest.fixture
async def make_client() -> AsyncIterator[AppFactory]:
    clients: list[httpx.AsyncClient] = []

    def factory(**overrides: object) -> httpx.AsyncClient:
        settings = make_settings(**overrides)
        app = create_app(settings, build_services(settings))
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        )
        clients.append(client)
        return client

    yield factory
    for client in clients:
        await client.aclose()


@pytest.fixture
def client(make_client: AppFactory, smartsheet: respx.MockRouter) -> httpx.AsyncClient:
    return make_client()


def writes(router: respx.MockRouter) -> list[httpx.Request]:
    """Solicitudes de escritura que llegaron a Smartsheet simulado."""
    return [call.request for call in router.calls if call.request.method != "GET"]
