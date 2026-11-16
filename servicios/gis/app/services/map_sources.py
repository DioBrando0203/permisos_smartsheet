"""Catálogo fijo de fuentes del mapa (SPEC-B14 punto 3): no llama a ningún servicio."""

from app.models.map import MapSource

SOURCES: tuple[MapSource, ...] = (
    MapSource(
        id="fdot_lrs",
        name="LRS Basemap Routes",
        provider="FDOT",
        url="https://gis.fdot.gov/",
        provides="Vía y milepost",
        update_frequency="Según FDOT",
        license_note="Datos públicos.",
    ),
    MapSource(
        id="fdot_boundaries",
        name="Límites administrativos",
        provider="FDOT",
        url="https://gis.fdot.gov/",
        provides="Condado, ciudad y ZIP",
        update_frequency="Según FDOT",
        license_note="Datos públicos.",
    ),
    MapSource(
        id="fdacs_parcels",
        name="Parcelas",
        provider="FDACS",
        url="https://gis.fdacs.gov/",
        provides="Parcela y uso de suelo",
        update_frequency="Según FDACS",
        license_note="Registro público; confirmar con el tasador.",
    ),
    MapSource(
        id="broward_parcels",
        name="Parcelas de Broward (respaldo)",
        provider="Broward County",
        url="https://services.arcgis.com/JMAJrTsHNLrSsWf5/ArcGIS/rest/services/Parcels",
        provides="Folio de la parcela cuando FDACS no responde",
        update_frequency="Según el condado",
        license_note="Datos públicos; condiciones de uso por revisar (MJ-PEN-06).",
    ),
    MapSource(
        id="stjohns_roads",
        name="Calles de St. Johns",
        provider="St. Johns County",
        url="https://www.gis.sjcfl.us/sjcgis/rest/services/Road/MapServer",
        provides="Quién mantiene cada calle del condado (MAINTENANCE)",
        update_frequency="Según el condado",
        license_note="Datos públicos; condiciones de uso por revisar (MJ-PEN-06).",
    ),
)
