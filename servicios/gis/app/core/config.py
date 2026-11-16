from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
    # Eje de calles de St. Johns con quién mantiene cada tramo (PEN-40, MJ-SJ-02).
    gis_stjohns_roads_url: str = "https://www.gis.sjcfl.us/sjcgis/rest/services/Road/MapServer/36"
    gis_trace_max_points: int = 100
    gis_timeout_seconds: float = 20.0
    # Un servidor que no acepta la conexión no se reintenta: sólo alargaría la espera (PEN-30).
    gis_connect_timeout_seconds: float = 5.0
    gis_unreachable_cooldown_seconds: float = 120.0
    gis_max_concurrency: int = 4
    gis_max_retries: int = 2
    gis_cache_ttl_seconds: float = 3600.0
    gis_max_segment_miles: float = 20.0
