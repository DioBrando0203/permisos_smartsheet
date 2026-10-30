"""Catálogo de capas ArcGIS públicas que consume el mapa."""

from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class Layer:
    id: str
    path: str
    fields: tuple[str, ...]
    with_route: bool = False


def layers(settings: Settings) -> tuple[Layer, ...]:
    """Devuelve URLs configurables para que las pruebas apunten a GIS simulado."""
    fdot = settings.gis_fdot_base_url.rstrip("/")
    boundaries = f"{fdot}/Admin_Boundaries/MapServer"
    roads = f"{fdot}/RCI_Layers/MapServer"
    return (
        Layer(
            "fdot_lrs",
            f"{roads}/8",
            ("ROADWAY", "COUNTY", "SECTION", "BEGIN_POST", "END_POST"),
            True,
        ),
        Layer(
            "fdot_state_roads",
            f"{roads}/15",
            ("ROADWAY", "ROUTE", "ROUTENUM", "DISTRICT", "COUNTYDOT", "COUNTY"),
        ),
        Layer(
            "fdot_county_roads",
            f"{roads}/2",
            ("ROADWAY", "ROUTE", "ROUTENUM", "DISTRICT", "COUNTYDOT", "COUNTY"),
        ),
        Layer("fdot_local_names", f"{roads}/13", ("ROADWAY", "NAME", "BEGIN_POST", "END_POST")),
        Layer("fdot_counties", f"{boundaries}/6", ("COUNTY", "CNTYNO", "DISTRICT")),
        Layer("fdot_cities", f"{boundaries}/7", ("NAME",)),
        Layer("fdot_zip", f"{boundaries}/8", ("ZIP",)),
        Layer(
            "fdacs_parcels",
            settings.gis_fdacs_parcels_url.rstrip("/"),
            ("CO_NO", "PARCEL_ID", "DOR_UC", "OWN_NAME"),
        ),
    )
