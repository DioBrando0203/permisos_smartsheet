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
            "attributes": {
                "ROADWAY": ROADWAY,
                "NAME": "LEJEUNE RD/NW 42 AVE",
                "COUNTY": "Miami-Dade",
                **_POSTS,
            },
            "paths": [ROUTE],
        }
    ],
}
# W Flagler St cruza la vía sintética en `START` (milepost 3.124), de oeste a este.
FLAGLER = [[-80.2700, START[0]], [-80.2500, START[0]]]
# Capa 6 de RCI (cruces): punto y milepost del cruce sobre la vía.
ROADS[6] = [
    {
        "attributes": {
            "ROADWAY": ROADWAY,
            "INTSEC_ROA": "SR- 968/W FLAGLER ST",
            "BEGIN_POST": 3.124,
            "COUNTY": "Miami-Dade",
        },
        "point": [START[1], START[0]],
    }
]

# Red separada del control para probar ajuste de dos puntos a tres vías consecutivas.
NETWORK_ROADS = [
    ("87001000", "SR 1001", [[-80.15, 26.099, 0.0], [-80.15, 26.102, 0.2]]),
    ("87002000", "SR 1002", [[-80.15, 26.102, 0.0], [-80.146, 26.102, 0.25]]),
    ("87003000", "SR 1003", [[-80.146, 26.102, 0.0], [-80.146, 26.105, 0.2]]),
]
for roadway, label, geometry in NETWORK_ROADS:
    attributes = {
        "ROADWAY": roadway,
        "COUNTY": "87",
        "SECTION": roadway[2:5],
        "BEGIN_POST": 0.0,
        "END_POST": geometry[-1][2],
    }
    ROADS[8].append({"attributes": attributes, "paths": [geometry]})
    ROADS[15].append(
        {"attributes": {**attributes, "ROUTE": label, "ROUTENUM": label[3:]}, "paths": [geometry]}
    )
    ROADS[13].append(
        {"attributes": {**attributes, "NAME": f"VIA SINTETICA {label}"}, "paths": [geometry]}
    )
# Calles TIGER del Censo por capa (2 interestatales, 6 avenidas, 8 locales): nombres con ordinal.
TIGER: dict[int, list[Json]] = {
    2: [],
    6: [{"attributes": {"NAME": "NW 42nd Ave"}, "paths": [[point[:2] for point in ROUTE]]}],
    8: [
        {"attributes": {"NAME": "W Flagler St"}, "paths": [FLAGLER]},
        # Paralela a la vía, unos 100 m al este: nunca la cruza.
        {"attributes": {"NAME": "NW 41st Ave"}, "paths": [[[p[0] + 0.001, p[1]] for p in ROUTE]]},
    ],
}


def _rectangle(west: float, south: float, east: float, north: float) -> list[list[float]]:
    return [[west, south], [east, south], [east, north], [west, north], [west, south]]


# Polígonos de Admin_Boundaries (6 condados, 7 ciudades, 8 ZIP, 13 distritos con Turnpike):
# en consultas por punto cubren cualquier punto. La vía sintética no está en el Turnpike.
BOUNDARIES: dict[int, Json] = {
    6: {"COUNTY": "Miami-Dade", "CNTYNO": "87", "DISTRICT": "6"},
    7: {"NAME": "Miami"},
    8: {"ZIP": "33126"},
    13: {"DVALUE": "D6", "SG_Distric": "District 6"},
}
# Contorno del condado cuando se pide con geometría (selector Condado del mapa).
COUNTY_RING = _rectangle(-80.30, 25.74, -80.22, 25.81)
# Ciudades del rectángulo del condado: un municipio (C1) y una zona no incorporada (U1) que
# el selector Ciudad debe descartar.
CITIES: list[Json] = [
    {
        "attributes": {
            "NAME": "Miami",
            "CLASSFP": "C1",
            "INTPTLAT": "+25.7750000",
            "INTPTLON": "-080.2600000",
        },
        "rings": [_rectangle(-80.28, 25.75, -80.24, 25.80)],
    },
    {
        "attributes": {
            "NAME": "Zona Sintetica",
            "CLASSFP": "U1",
            "INTPTLAT": "+25.7900000",
            "INTPTLON": "-080.2900000",
        },
        "rings": [_rectangle(-80.30, 25.78, -80.28, 25.80)],
    },
]


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
# El geocodificador sólo reconoce el cruce con W Flagler St y direcciones sobre la vía sintética.
CROSSING: Json = {
    "matchedAddress": "W FLAGLER ST & NW 42ND AVE, MIAMI, FL, 33126",
    "coordinates": {"x": START[1], "y": START[0]},
}
ADDRESS: Json = {
    "matchedAddress": "1000 NW 42ND AVE, MIAMI, FL, 33126",
    "coordinates": {"x": -80.263768, "y": 25.775926},
}
