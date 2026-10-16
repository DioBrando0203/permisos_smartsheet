from app.core.config import split_list
from tests.conftest import FAKE_TOKEN, make_settings
from tests.factories import SHEET_ID


async def test_foreign_origin_cannot_write(client, smartsheet) -> None:
    response = await client.delete(
        f"/api/sheets/{SHEET_ID}/shares/S-ANA", headers={"Origin": "https://otro.example"}
    )
    assert response.json()["detail"]["code"] == "ORIGIN_NOT_ALLOWED"
    assert smartsheet.calls.call_count == 0


async def test_foreign_host_is_rejected(client) -> None:
    response = await client.get("/api/health", headers={"Host": "evil.example"})
    assert response.status_code == 400


async def test_health_reports_read_only_without_calling_smartsheet(make_client, smartsheet) -> None:
    client = make_client(app_read_only=True)
    body = (await client.get("/api/health")).json()
    assert body == {"status": "ok", "smartsheet": "configured", "read_only": True}
    assert smartsheet.calls.call_count == 0


def test_token_is_secret() -> None:
    settings = make_settings()
    assert FAKE_TOKEN not in repr(settings)
    assert FAKE_TOKEN not in str(settings.model_dump())


def test_read_only_is_the_default() -> None:
    from app.core.config import Settings

    assert Settings(_env_file=None).app_read_only is True


def test_lists_from_environment() -> None:
    assert split_list(" 192.168.1.20 , localhost,,") == ("192.168.1.20", "localhost")


def test_httpx_does_not_log_full_urls() -> None:
    import logging

    import app.main  # noqa: F401  configura los registros al importar

    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING


def test_every_endpoint_has_a_single_swagger_group() -> None:
    from app.main import create_app

    spec = create_app(make_settings(), frontend_dist=None).openapi()
    tags = {path: op.get("tags") for path, ops in spec["paths"].items() for op in ops.values()}
    assert all(len(group or []) == 1 for group in tags.values()), tags
    assert tags["/api/review"] == ["auditoría y comparación"]
