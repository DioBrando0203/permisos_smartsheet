"""Catálogo de capas ArcGIS públicas que consume el mapa."""

from dataclasses import dataclass

from app.core.config import Settings

LRS, STATE_ROADS, COUNTY_ROADS, LOCAL_NAMES = 8, 15, 2, 13
# Broward: código del FDOT (CNTYNO) y del DOR (CO_NO), que no coinciden (MJ-PE-02).
BROWARD_FDOT, BROWARD_DOR = "86", "16"


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


def broward_parcels(settings: Settings) -> Layer:
    """Parcelas del condado de Broward: sólo el folio, sin datos del tasador (MJ-BR-01)."""
    return Layer("broward_parcels", settings.gis_broward_parcels_url.rstrip("/"), ("FOLIO",))


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
