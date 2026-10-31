"""Lectura pura de lo que la persona escribe en el buscador del mapa (sin E/S)."""

import re
from dataclasses import dataclass

_NUMBER = r"[0-9]{1,3}(?:\.[0-9]+)?"
_SEPARATOR = r"(?:\s*(?:,|MP|MILEPOST|MILE\s+POST)\s*|\s+)"
_COORDINATES = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*[,\s]\s*(-?\d{1,3}(?:\.\d+)?)\s*$")
_ROUTE = re.compile(
    rf"^\s*(SR|CR|S\.R\.|C\.R\.)\s*-?\s*(A1A|[0-9]{{1,4}}[A-Z]?){_SEPARATOR}({_NUMBER})\s*$",
    re.IGNORECASE,
)
_ROADWAY = re.compile(rf"^\s*([0-9]{{8}}){_SEPARATOR}({_NUMBER})\s*$", re.IGNORECASE)
_ADDRESS = re.compile(r"^\s*[0-9]+[A-Z]?\s+[A-Z]", re.IGNORECASE)
_STATE = re.compile(r"\b(FL|FLORIDA)\b", re.IGNORECASE)
_ORDINAL = re.compile(r"\b([0-9]+)(ST|ND|RD|TH)\b")
# Cruce de calles: "Las Olas & 3rd Ave", "Las Olas y 3rd Ave", "Broward Blvd at Andrews".
_CROSSING = re.compile(r"\s*&\s*|\s+(?:and|y|at|con|x)\s+", re.IGNORECASE)
# FDOT escribe los nombres abreviados y sin ordinales: "NW 42 AVE", "W FLAGLER ST".
_ABBREVIATIONS = {
    "AVENUE": "AVE",
    "STREET": "ST",
    "ROAD": "RD",
    "BOULEVARD": "BLVD",
    "DRIVE": "DR",
    "HIGHWAY": "HWY",
    "PARKWAY": "PKWY",
    "TERRACE": "TER",
    "COURT": "CT",
    "PLACE": "PL",
    "LANE": "LN",
}


@dataclass(frozen=True)
class RouteQuery:
    system: str  # "SR", "CR" o "ROADWAY"
    number: str
    milepost: float


def parse_coordinates(text: str) -> tuple[float, float] | None:
    """`25.771778, -80.263610` o `25.771778 -80.263610` (latitud primero, como Google Maps)."""
    match = _COORDINATES.match(text)
    if not match:
        return None
    lat, lon = float(match[1]), float(match[2])
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None


def parse_route_milepost(text: str) -> RouteQuery | None:
    """`SR 953 3.5`, `SR-953 MP 3.5`, `CR 811, 0.3` o un ID de vía de 8 dígitos con milepost."""
    if match := _ROADWAY.match(text):
        return RouteQuery("ROADWAY", match[1], float(match[2]))
    if match := _ROUTE.match(text):
        system = "SR" if match[1].upper().startswith("S") else "CR"
        return RouteQuery(system, match[2].upper(), float(match[3]))
    return None


def route_where(query: RouteQuery) -> str:
    """Filtro ArcGIS seguro: el número ya pasó por la expresión regular."""
    field = "ROADWAY" if query.system == "ROADWAY" else "ROUTENUM"
    return f"{field} = '{query.number}'"


def street_text(text: str) -> str | None:
    """Nombre como lo escribe FDOT, con sólo letras, números y `/ . & -`; nunca comillas."""
    words = re.sub(r"[^A-Z0-9 /.&-]", " ", text.upper()).split()
    cleaned = _ORDINAL.sub(r"\1", " ".join(_ABBREVIATIONS.get(word, word) for word in words))
    return cleaned if len(cleaned) >= 3 else None


def street_where(text: str, field: str = "NAME") -> str | None:
    cleaned = street_text(text)
    return word_like(field, cleaned) if cleaned else None


def word_like(field: str, pattern: str) -> str:
    """`LIKE` que empieza en una palabra: "3 AVE" no debe encontrar "SE 13 AVE".

    Vale al inicio del nombre, tras un espacio o tras `/` ("LEJEUNE RD/NW 42 AVE").
    """
    options = (f"UPPER({field}) LIKE '{prefix}{pattern}%'" for prefix in ("", "% ", "%/"))
    return f"({' OR '.join(options)})"


def street_rank(name: str, cleaned: str) -> tuple[int, int, int]:
    """Primero calles que empiezan por lo buscado; rampas y conectores (`X TO Y`) al final."""
    ramp = bool(re.search(r"\bTO\b|\bTO[0-9]", name))
    starts = any(part.strip().startswith(cleaned) for part in name.split("/"))
    return int(ramp), int(not starts), len(name)


def looks_like_address(text: str) -> bool:
    """Una dirección empieza con número de casa: `200 E Las Olas Blvd`."""
    return bool(_ADDRESS.match(text))


def address_text(text: str, city: str | None = None) -> str:
    """El geocodificador del Censo cubre todo EE. UU.: se acota a la ciudad elegida y a Florida.

    Sólo una ciudad ayuda; el nombre de un condado en esa posición hace fallar la coincidencia.
    """
    if _STATE.search(text):
        return text
    if city and city.upper() not in text.upper():
        return f"{text}, {city}, FL"
    return f"{text}, FL"


def join_parts(*parts: str | None) -> str:
    return " · ".join(part for part in parts if part)


def parse_intersection(text: str) -> tuple[str, str] | None:
    """Dos calles separadas por `&`, `and`, `y`, `at`, `con` o `x`; cada una de 3 letras o más."""
    parts = [part.strip() for part in _CROSSING.split(text, maxsplit=1)]
    if len(parts) != 2 or any(len(part) < 3 for part in parts):
        return None
    return parts[0], parts[1]


def tiger_where(text: str) -> str | None:
    """Filtro para nombres del Censo ("SE 3rd Ave"): un número acepta su ordinal (`3%`)."""
    cleaned = street_text(text)
    if not cleaned:
        return None
    pattern = " ".join(f"{word}%" if word.isdigit() else word for word in cleaned.split())
    return word_like("NAME", pattern)


def name_where(field: str, value: str) -> str:
    """Igualdad con un nombre que dio la propia fuente (condado, ciudad); duplica comillas."""
    escaped = value.replace("'", "''")
    return f"{field} = '{escaped}'"
