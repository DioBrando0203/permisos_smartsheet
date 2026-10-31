"""Backend real para E2E, apuntado al Smartsheet falso y al GIS falso (ADR-10 del frontend).

Ningún valor que importe sale de `backend/.env`, que tiene el token real: se fijan aquí y ganan
al `.env` y a las variables de entorno (importar `app.main` crea también la app por defecto, que
no se sirve ni hace solicitudes). Solo lectura, como el panel (ADR-B11).
Lo arranca `frontend/playwright.config.ts`; uso manual desde `backend/`:
`python -m tests.e2e_backend --port 8793 --smartsheet 8791 --gis 8792 --frontend 5791`.
"""

import argparse

import uvicorn
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app

HOST = "127.0.0.1"


def e2e_settings(port: int, smartsheet: int, gis: int, frontend: int) -> Settings:
    fake_gis = f"http://{HOST}:{gis}"
    return Settings(
        _env_file=None,
        smartsheet_access_token=SecretStr("fake-token"),
        smartsheet_base_url=f"http://{HOST}:{smartsheet}/2.0",
        smartsheet_retry_base_seconds=0.0,
        app_read_only=True,
        app_port=port,
        app_allowed_origins=f"http://{HOST}:{frontend},http://localhost:{frontend}",
        app_dynamic_view_sheets="",
        app_designer_catalog_sheet="",
        gis_fdot_base_url=f"{fake_gis}/arcgis/rest/services",
        gis_fdacs_parcels_url=f"{fake_gis}/fdacs/parcels/0",
        gis_census_geocoder_url=f"{fake_gis}/census/onelineaddress",
        gis_broward_parcels_url=f"{fake_gis}/broward/parcels/0",
        gis_max_retries=0,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backend para E2E contra los servicios falsos")
    parser.add_argument("--port", type=int, default=8793)
    parser.add_argument("--smartsheet", type=int, default=8791)
    parser.add_argument("--gis", type=int, default=8792)
    parser.add_argument("--frontend", type=int, default=5791)
    args = parser.parse_args()
    settings = e2e_settings(args.port, args.smartsheet, args.gis, args.frontend)
    uvicorn.run(create_app(settings, frontend_dist=None), host=HOST, port=args.port)
