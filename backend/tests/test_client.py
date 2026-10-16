import logging

import httpx
import pytest
import respx

from app.core.errors import AppError
from app.services.permissions import AccessLevel
from app.services.smartsheet import NewShare, SmartsheetClient
from tests.conftest import BASE, FAKE_TOKEN, make_settings


@pytest.fixture
async def ss_client():
    client = SmartsheetClient(make_settings())
    yield client
    await client.aclose()


async def test_token_is_sent_and_never_logged(ss_client, caplog) -> None:
    caplog.set_level(logging.INFO)
    with respx.mock(base_url=BASE) as router:
        route = router.get("/users/me").respond(json={"id": 1, "email": "a@example.com"})
        await ss_client.get_me()
    assert route.calls.last.request.headers["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert FAKE_TOKEN not in caplog.text
    assert "smartsheet GET /users/me -> 200" in caplog.text


async def test_rate_limit_retries_then_fails(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        route = router.get("/users/me").respond(429, json={"errorCode": 4003, "refId": "r1"})
        with pytest.raises(AppError) as error:
            await ss_client.get_me()
    assert error.value.code == "SMARTSHEET_RATE_LIMITED"
    assert route.call_count == 3  # 1 intento + 2 reintentos (make_settings)


async def test_read_retries_on_500_then_succeeds(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        router.get("/users/me").mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(200, json={"id": 1, "email": "a@x.io"}),
            ]
        )
        me = await ss_client.get_me()
    assert me.user_id == "1"


async def test_writes_are_not_retried_on_500(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        route = router.post("/shares").respond(500)
        with pytest.raises(AppError) as error:
            share = NewShare("a@example.com", None, AccessLevel.VIEWER)
            await ss_client.create_sheet_shares("1", [share], None)
    assert error.value.code == "SMARTSHEET_UNAVAILABLE"
    assert route.call_count == 1


async def test_follows_last_key(ss_client) -> None:
    first = {
        "items": [{"id": "A", "accessLevel": "VIEWER", "email": "a@example.com"}],
        "lastKey": "k2",
    }
    second = {"items": [{"id": "B", "accessLevel": "EDITOR", "email": "b@example.com"}]}
    with respx.mock(base_url=BASE) as router:
        route = router.get("/shares").mock(
            side_effect=[httpx.Response(200, json=first), httpx.Response(200, json=second)]
        )
        shares = await ss_client.list_sheet_shares("1")
    assert [share.id for share in shares] == ["A", "B"]
    assert route.calls.last.request.url.params["lastKey"] == "k2"


async def test_auth_error_is_translated(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        router.get("/sheets").respond(401, json={"errorCode": 1002, "refId": "abc"})
        with pytest.raises(AppError) as error:
            await ss_client.list_sheets()
    assert (error.value.code, error.value.ref_id, error.value.status) == (
        "SMARTSHEET_AUTH",
        "abc",
        502,
    )
    assert FAKE_TOKEN not in error.value.message


async def test_missing_token_never_calls_smartsheet() -> None:
    client = SmartsheetClient(make_settings(smartsheet_access_token=None))
    with respx.mock(base_url=BASE) as router:
        with pytest.raises(AppError) as error:
            await client.list_sheets()
    assert error.value.code == "TOKEN_MISSING"
    assert router.calls.call_count == 0
    await client.aclose()


def _page(number: int, ids: range, total_pages: int, size: int = 100) -> httpx.Response:
    items = [{"id": n, "email": f"p{n}@example.com"} for n in ids]
    body = {"pageNumber": number, "pageSize": size, "totalPages": total_pages, "data": items}
    return httpx.Response(200, json=body)


async def test_pagination_without_include_all(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        route = router.get("/contacts").mock(
            side_effect=[_page(1, range(100), 2), _page(2, range(100, 130), 2)]
        )
        contacts = await ss_client.list_contacts()
    assert len(contacts) == 130
    params = [call.request.url.params for call in route.calls]
    assert [p["page"] for p in params] == ["1", "2"]
    assert all("includeAll" not in p and p["pageSize"] == "100" for p in params)


async def test_unknown_total_stops_on_empty_page_zero(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        route = router.get("/users").mock(
            side_effect=[
                _page(1, range(100), -1),
                _page(2, range(100, 200), -1),
                _page(0, range(0), 0),
            ]
        )
        users = await ss_client.list_users()
    assert len(users) == 200 and route.call_count == 3


async def test_repeated_last_page_is_not_duplicated(ss_client) -> None:
    with respx.mock(base_url=BASE) as router:
        route = router.get("/groups").mock(
            side_effect=[_page(1, range(100), -1), _page(1, range(100), -1)]
        )
        groups = await ss_client.list_groups()
    assert len(groups) == 100 and route.call_count == 2
