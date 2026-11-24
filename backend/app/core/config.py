"""Configuración inmutable leída del entorno y de `backend/.env`.

El token se guarda como `SecretStr` para que nunca aparezca en `repr`, logs ni errores (SM-01).
"""

from functools import lru_cache
from typing import Literal

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
    # Freno propio por debajo de los 300 por minuto de Smartsheet: evita el 429 y deja margen a
    # otros usos del mismo token (SPEC-B21 CA-02).
    smartsheet_max_requests_per_minute: int = 250
    # Eventos que guarda el registro en memoria de `/api/ids/logs` (SPEC-B21 RG-01).
    app_log_buffer_size: int = 1000
    cache_ttl_seconds: float = 120.0
    # Activo por defecto: escribir en Smartsheet exige desactivarlo a propósito (ADR-B11).
    app_read_only: bool = True
    ids_admin_token: SecretStr | None = None
    # Base del servicio en un servidor (Railway u otro, SPEC-B22 DP-03), como URL con su clave;
    # vacía: la local del equipo Linux (B-16). Secreta como el token: nunca en logs ni errores.
    ids_database_url: SecretStr | None = None
    ids_monitor_enabled: bool = False
    ids_monitor_interval_seconds: int = 60
    # Consulta liviana de cambios entre ciclos (segundos); 0 la desactiva.
    ids_monitor_poll_seconds: int = 5
    # Sin cambios por este tiempo, la consulta pasa a ser lenta (noches y horas sin trabajo):
    # evita gastar llamadas mirando una hoja quieta (SPEC-B21 CA-05).
    ids_monitor_idle_after_seconds: int = 120
    ids_monitor_idle_poll_seconds: int = 30
    ids_writes_enabled: bool = False
    ids_transition_approved: bool = False
    ids_approved_starts: str = "{}"
    # Procesador con asignación real: exige además las tres barreras anteriores.
    ids_processor_writes_enabled: bool = False
    ids_processor_max_rows: int = 5
    # Hoja maestra del ID Manager, Obs y catálogo (PEN-48). Cambiarla exige trasladar antes el
    # registro con `servicios/ids/mover_hoja_maestra.py`, con el backend detenido.
    ids_master_sheet_id: str = "5254686035890052"
    # Cambio de cliente (SPEC-ID01 ID-44 a ID-47): ID nuevo, hijas ajenas fuera y hijas al día.
    ids_customer_change_enabled: bool = False
    # Formato del ID de proyecto (SPEC-ID01 ID-52): `customer` (KMV-CC-26-001) o `year`
    # (KMV-26-0001, maestra 2.0, PEN-54): un contador por año y empresa, sin cliente.
    ids_project_format: Literal["customer", "year"] = "customer"
    # Listas de `Parent Project` y `Linked Tracking` al día con los proyectos (ID-54).
    ids_project_options_enabled: bool = False
    # Hoja catálogo de proyectos en Pruebas, origen del desplegable vinculado de Linked Tracking.
    app_project_catalog_sheet: str = ""
    # Conversaciones de cada fila copiadas a Obs (SPEC-B17); exige las barreras de escritura.
    app_obs_sync_enabled: bool = False
    app_obs_column: str = "Obs"
    app_obs_timezone: str = "America/Lima"
    app_obs_interval_seconds: int = 30
    app_obs_max_rows: int = 20
    # También las conversaciones de las hojas de equipo marcadas en su spec (hoy `Permits`), en
    # el `Obs` de su fila de la maestra (SPEC-B17 OB-17); exige esa hoja activada.
    app_obs_mirrors_enabled: bool = False
    # Un paso cuyas hojas no cambiaron se salta, pero corre igual cada tanto por si algo no
    # movió la versión (SPEC-B21 CA-03, CA-04); Obs más seguido: una conversación nueva quizá
    # no cambie la versión de la hoja.
    app_steps_force_seconds: int = 600
    app_obs_force_seconds: int = 120
    # Hoja hija de Records (SPEC-B18): exige las barreras de escritura del ID Manager.
    app_records_sync_enabled: bool = False
    app_records_sheet_id: str = ""
    app_records_interval_seconds: int = 30
    app_records_max_rows: int = 20
    # Hoja hija de Facturación (SPEC-B19); usa el mismo intervalo y tope que Records.
    app_billing_sync_enabled: bool = False
    app_billing_sheet_id: str = ""
    # Metraje editable en la maestra y en `Billing`, con aviso por correo (SPEC-B19 FH-05c).
    app_footage_sync_enabled: bool = False
    # Hijas de la maestra completan sus celdas vacías con las de su proyecto (SPEC-B20 HP-07).
    app_inherit_enabled: bool = False
    # Hojas de proceso (SPEC-B20, PEN-54): permisos, y MOT con paquetes; mismo tope que Records.
    app_permits_sync_enabled: bool = False
    app_permits_sheet_id: str = ""
    app_mot_sync_enabled: bool = False
    app_mot_sheet_id: str = ""
    # Hoja de Design Ticket y Mile Post (SPEC-B20 HP-14): una fila por proyecto con `DT Owner`.
    app_design_tickets_sync_enabled: bool = False
    app_design_tickets_sheet_id: str = ""
    # Listas de las columnas de asignación desde el directorio `Contact List` (SPEC-B20 HP-19).
    app_contact_options_enabled: bool = False
    app_contacts_sheet_id: str = ""
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

    @property
    def has_token(self) -> bool:
        token = self.smartsheet_access_token
        return token is not None and bool(token.get_secret_value().strip())

    @property
    def database_url(self) -> str | None:
        if self.ids_database_url is None:
            return None
        return self.ids_database_url.get_secret_value().strip() or None

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
