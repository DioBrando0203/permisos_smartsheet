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
    app_allowed_origins: str = _DEFAULT_ORIGINS

    @property
    def has_token(self) -> bool:
        token = self.smartsheet_access_token
        return token is not None and bool(token.get_secret_value().strip())

    @property
    def allowed_hosts(self) -> tuple[str, ...]:
        return split_list(self.app_allowed_hosts) or split_list(_DEFAULT_HOSTS)

    @property
    def allowed_origins(self) -> tuple[str, ...]:
        return split_list(self.app_allowed_origins) or split_list(_DEFAULT_ORIGINS)


def split_list(raw: str) -> tuple[str, ...]:
    """Lista separada por comas, sin espacios ni elementos vacíos."""
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
