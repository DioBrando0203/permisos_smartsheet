"""El backend del E2E nunca hereda el token ni las URL reales del entorno o de `.env`."""

import pytest

from tests.e2e_backend import e2e_settings


def test_e2e_settings_ignore_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMARTSHEET_ACCESS_TOKEN", "token-del-entorno")
    monkeypatch.setenv("SMARTSHEET_BASE_URL", "https://api.smartsheet.com/2.0")
    monkeypatch.setenv("APP_READ_ONLY", "false")
    monkeypatch.setenv("GIS_FDOT_BASE_URL", "https://gis.fdot.gov/arcgis/rest/services")
    settings = e2e_settings(port=8793, smartsheet=8791, gis=8792, frontend=5791)
    assert settings.smartsheet_access_token is not None
    assert settings.smartsheet_access_token.get_secret_value() == "fake-token"
    assert settings.smartsheet_base_url == "http://127.0.0.1:8791/2.0"
    assert settings.app_read_only is True
    gis_urls = (
        settings.gis_fdot_base_url,
        settings.gis_fdacs_parcels_url,
        settings.gis_census_geocoder_url,
        settings.gis_broward_parcels_url,
        settings.gis_miami_dade_parcels_url,
    )
    assert all(url.startswith("http://127.0.0.1:8792/") for url in gis_urls)
    assert "http://127.0.0.1:5791" in settings.allowed_origins
