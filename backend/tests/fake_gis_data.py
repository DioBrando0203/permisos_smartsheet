"""Datos sintéticos del GIS falso (SPEC-B14, ADR-10 del frontend).

La vía imita el caso de control de OSP: SR 953, vía 87281000, sección 281, milepost 3.124 en
`START` y 3.839 en `END`, prolongada un tramo igual hacia cada lado. Límites, parcela y
dirección son de mentira y el propietario es sintético.
"""

from typing import Any

Json = dict[str, Any]
ROADWAY = "87281000"
START = (25.771778, -80.26361)
END = (25.782147, -80.264005)
# [lon, lat, milepost], como devuelve la capa 8 con `returnM=true`.
ROUTE = [
    [-80.263215, 25.761409, 2.409],
    [-80.26361, 25.771778, 3.124],
    [-80.264005, 25.782147, 3.839],
    [-80.2644, 25.792516, 4.554],
]
# Más cerca que esto de la vía, FDACS no da predio: el clic cayó sobre la calzada.
ROAD_PARCEL_METERS = 12.0
_POSTS = {"BEGIN_POST": 2.409, "END_POST": 4.554}

# Capas de líneas de RCI_Layers por número (8 LRS, 15 estatales, 2 de condado, 13 nombres).
ROADS: dict[int, list[Json]] = {
    8: [
        {
            "attributes": {"ROADWAY": ROADWAY, "COUNTY": "87", "SECTION": "281", **_POSTS},
            "paths": [ROUTE],
        }
    ],
    15: [
        {
            "attributes": {
                "ROADWAY": ROADWAY,
                "ROUTE": "SR  953",
                "ROUTENUM": "953",
                "DISTRICT": "6",
                "COUNTYDOT": "87",
                "COUNTY": "Miami-Dade",
                **_POSTS,
            },
            "paths": [ROUTE],
        }
    ],
    2: [],
    13: [
        {
            "attributes": {"ROADWAY": ROADWAY, "NAME": "LEJEUNE RD/NW 42 AVE", **_POSTS},
            "paths": [ROUTE],
        }
    ],
}
# Polígonos de Admin_Boundaries (6 condados, 7 ciudades, 8 ZIP, 13 distritos con Turnpike):
# cubren cualquier punto. La vía sintética no está en el Turnpike (distrito 6, no D8).
BOUNDARIES: dict[int, Json] = {
    6: {"COUNTY": "Miami-Dade", "CNTYNO": "87", "DISTRICT": "6"},
    7: {"NAME": "Miami"},
    8: {"ZIP": "33126"},
    13: {"DVALUE": "D6", "SG_Distric": "District 6"},
}


def _lot(folio: str, south: float, north: float) -> Json:
    """Lote rectangular de unos 45 m al este de la vía sintética (sólo para dibujar)."""
    west, east = -80.26330, -80.26285
    ring = [[west, south], [east, south], [east, north], [west, north], [west, south]]
    return {"attributes": {"FOLIO": folio}, "rings": [ring]}


# Contornos de Miami-Dade (capa 26 de MD_LandInformation) junto al caso de control.
MIAMI_DADE_LOTS: list[Json] = [
    _lot(f"30000000000{index}", 25.7720 + index * 0.0004, 25.7724 + index * 0.0004)
    for index in range(4)
]
ROAD_GAP: Json = {"CO_NO": 0.0, "PARCEL_ID": "", "DOR_UC": "", "OWN_NAME": ""}
PARCEL: Json = {
    "CO_NO": 23.0,
    "PARCEL_ID": "0000000000001",
    "DOR_UC": "001",
    "OWN_NAME": "PROPIETARIO SINTETICO 1",
}
# Respaldo del condado de Broward (sólo el folio); la vía sintética está en Miami-Dade.
BROWARD_PARCEL: Json = {"FOLIO": "000000000001"}
# El geocodificador sólo reconoce direcciones sobre la vía sintética.
ADDRESS: Json = {
    "matchedAddress": "1000 NW 42ND AVE, MIAMI, FL, 33126",
    "coordinates": {"x": -80.263768, "y": 25.775926},
}
