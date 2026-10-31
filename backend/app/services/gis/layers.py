"""Catálogo de capas ArcGIS públicas que consume el mapa."""

from dataclasses import dataclass

from app.core.config import Settings

LRS, STATE_ROADS, COUNTY_ROADS, LOCAL_NAMES = 8, 15, 2, 13
# Admin_Boundaries: condados y distritos del FDOT con el Turnpike (D8, FTE; GIS-PEN-01).
COUNTIES, TURNPIKE_DISTRICTS, TURNPIKE = 6, 13, "D8"
# Broward: código del FDOT (CNTYNO) y del DOR (CO_NO), que no coinciden (MJ-PE-02).
BROWARD_FDOT, BROWARD_DOR = "86", "16"
MIAMI_DADE_FDOT = "87"


@dataclass(frozen=True)
class Layer:
    id: str
    path: str
    fields: tuple[str, ...]
    with_route: bool = False
    # Sólo las líneas usan radio: con `distance=0` FDOT y FDACS devuelven vacío en polígonos.
    radius: bool = False


def road_layer(settings: Settings, number: int) -> str:
    """URL de una capa de vías del FDOT (RCI), configurable para pruebas."""
    return f"{settings.gis_fdot_base_url.rstrip('/')}/RCI_Layers/MapServer/{number}"


def boundary_layer(settings: Settings, number: int) -> str:
    """URL de una capa de límites del FDOT (Admin_Boundaries)."""
    return f"{settings.gis_fdot_base_url.rstrip('/')}/Admin_Boundaries/MapServer/{number}"


def broward_parcels(settings: Settings) -> Layer:
    """Parcelas del condado de Broward: sólo el folio, sin datos del tasador (MJ-BR-01)."""
    return Layer("broward_parcels", settings.gis_broward_parcels_url.rstrip("/"), ("FOLIO",))


def parcel_outline_layer(settings: Settings, county_fdot: str | None) -> Layer:
    """Contornos de parcelas: el condado si tiene fuente verificada (PEN-33); si no, FDACS.

    El único campo es el ID: dibujar límites no necesita propietario ni datos del tasador.
    """
    if county_fdot == BROWARD_FDOT:
        return broward_parcels(settings)
    if county_fdot == MIAMI_DADE_FDOT:
        url = settings.gis_miami_dade_parcels_url.rstrip("/")
        return Layer("miami_dade_parcels", url, ("FOLIO",))
    return Layer("fdacs_parcels", settings.gis_fdacs_parcels_url.rstrip("/"), ("PARCEL_ID",))


def layers(settings: Settings) -> tuple[Layer, ...]:
    """Devuelve URLs configurables para que las pruebas apunten a GIS simulado."""
    boundaries = f"{settings.gis_fdot_base_url.rstrip('/')}/Admin_Boundaries/MapServer"
    road_fields = ("ROADWAY", "ROUTE", "ROUTENUM", "DISTRICT", "COUNTYDOT", "COUNTY")
    return (
        Layer(
            "fdot_lrs",
            road_layer(settings, LRS),
            ("ROADWAY", "COUNTY", "SECTION", "BEGIN_POST", "END_POST"),
            with_route=True,
            radius=True,
        ),
        Layer("fdot_state_roads", road_layer(settings, STATE_ROADS), road_fields, radius=True),
        Layer("fdot_county_roads", road_layer(settings, COUNTY_ROADS), road_fields, radius=True),
        Layer(
            "fdot_local_names",
            road_layer(settings, LOCAL_NAMES),
            ("ROADWAY", "NAME", "BEGIN_POST", "END_POST"),
            radius=True,
        ),
        Layer("fdot_counties", f"{boundaries}/6", ("COUNTY", "CNTYNO", "DISTRICT")),
        Layer("fdot_cities", f"{boundaries}/7", ("NAME",)),
        Layer("fdot_zip", f"{boundaries}/8", ("ZIP",)),
        Layer(
            "fdacs_parcels",
            settings.gis_fdacs_parcels_url.rstrip("/"),
            ("CO_NO", "PARCEL_ID", "DOR_UC", "OWN_NAME"),
        ),
    )
