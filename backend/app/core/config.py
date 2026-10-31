"""Configuración inmutable leída del entorno y de `backend/.env`.

El token se guarda como `SecretStr` para que nunca aparezca en `repr`, logs ni errores (SM-01).
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_HOSTS = "localhost,127.0.0.1,[::1]"
_DEFAULT_ORIGINS = (
    "http://localhost:5710,http://127.0.0.1:5710,http://localhost:8710,http://127.0.0.1:8710"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    app_name: str = "Permisos de Smartsheet"
    smartsheet_access_token: SecretStr | None = None
    smartsheet_base_url: str = "https://api.smartsheet.com/2.0"
    smartsheet_timeout_seconds: float = 20.0
    # Smartsheet admite 300 solicitudes por minuto por token; más concurrencia sólo provoca 429.
    smartsheet_max_concurrency: int = 8
    smartsheet_max_retries: int = 4
    smartsheet_retry_base_seconds: float = 1.0
    cache_ttl_seconds: float = 120.0
    # Activo por defecto: escribir en Smartsheet exige desactivarlo a propósito (ADR-B11).
    app_read_only: bool = True
    app_allowed_hosts: str = _DEFAULT_HOSTS
    # Hojas con Dynamic View, marcadas a mano: la API no lo expone (B-07, PEN-17).
    app_dynamic_view_sheets: str = ""
    app_allowed_origins: str = _DEFAULT_ORIGINS
    # Puerto real en que arrancó (lo fija run.py, que puede elegir uno libre al azar):
    # sus orígenes se permiten para que Swagger pueda escribir desde ese mismo puerto.
    app_port: int | None = None
    # Carga de diseñadores (SPEC-B12): columnas, estado y qué estados cuentan como cerrados.
    app_designer_columns: str = "Designer1,Designer2"
    app_status_column: str = "Project Status"
    app_closed_statuses: str = (
        "CANCELLED,COMPLETE,8. Process completed,4. Permit Cancelled,4. Permit Closed,"
        "4. No Permit Required,NO PERMIT REQUIRED"
    )
    app_designer_catalog_sheet: str = ""
    app_designer_catalog_column: str = "Designer"
    # GIS público: se mantiene aislado del transporte de Smartsheet para no filtrar el token.
    app_gis_enabled: bool = True
    gis_fdot_base_url: str = "https://gis.fdot.gov/arcgis/rest/services"
    gis_fdacs_parcels_url: str = (
        "https://gis.fdacs.gov/mapping/rest/services/GIO_Parcels_for_OAWP_Optimized/FeatureServer/0"
    )
    gis_census_geocoder_url: str = (
        "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    )
    # Respaldo de parcelas en Broward cuando FDACS falla (PEN-30, MJ-BR-01).
    gis_broward_parcels_url: str = (
        "https://services.arcgis.com/JMAJrTsHNLrSsWf5/ArcGIS/rest/services/Parcels/FeatureServer/0"
    )
    # Parcelas para dibujar límites en Miami-Dade (PEN-33); Broward usa la URL de arriba.
    gis_miami_dade_parcels_url: str = (
        "https://gisweb.miamidade.gov/arcgis/rest/services/MD_LandInformation/MapServer/26"
    )
    # Calles de todo EE. UU. (TIGER del Censo): el buscador las usa sólo dentro de un condado.
    gis_tiger_roads_url: str = (
        "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer"
    )
    gis_trace_max_points: int = 100
    gis_timeout_seconds: float = 20.0
    # Un servidor que no acepta la conexión no se reintenta: sólo alargaría la espera (PEN-30).
    gis_connect_timeout_seconds: float = 5.0
    gis_unreachable_cooldown_seconds: float = 120.0
    gis_max_concurrency: int = 4
    gis_max_retries: int = 2
    gis_cache_ttl_seconds: float = 3600.0
    gis_max_segment_miles: float = 20.0

    @property
    def has_token(self) -> bool:
        token = self.smartsheet_access_token
        return token is not None and bool(token.get_secret_value().strip())

    @property
    def allowed_hosts(self) -> tuple[str, ...]:
        return split_list(self.app_allowed_hosts) or split_list(_DEFAULT_HOSTS)

    @property
    def dynamic_view_sheets(self) -> frozenset[str]:
        return frozenset(split_list(self.app_dynamic_view_sheets))

    @property
    def allowed_origins(self) -> tuple[str, ...]:
        origins = split_list(self.app_allowed_origins) or split_list(_DEFAULT_ORIGINS)
        if self.app_port is None:
            return origins
        own = tuple(f"http://{host}:{self.app_port}" for host in ("127.0.0.1", "localhost"))
        return origins + tuple(origin for origin in own if origin not in origins)


def split_list(raw: str) -> tuple[str, ...]:
    """Lista separada por comas, sin espacios ni elementos vacíos."""
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
