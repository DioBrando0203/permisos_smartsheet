"""Contrato HTTP del mapa GIS; no contiene respuestas crudas de ArcGIS."""

from typing import Literal

from pydantic import BaseModel


class RoadMatch(BaseModel):
    roadway_id: str
    county_code_fdot: str | None = None
    section: str | None = None
    subsection: str | None = None
    kind: Literal["state", "county", "other"]
    route: str | None = None
    local_name: str | None = None
    milepost: float | None = None
    distance_m: float
    begin_post: float | None = None
    end_post: float | None = None


class MapLocation(BaseModel):
    county: str | None = None
    county_code_fdot: str | None = None
    fdot_district: str | None = None
    # Sólo municipios; un lugar censal no incorporado (Nocatee) va a `place` (PEN-40).
    city: str | None = None
    # Tipo del municipio según el Censo (LSAD): city, town o village (PEN-41).
    municipality_type: Literal["city", "town", "village"] | None = None
    place: str | None = None
    zip: str | None = None


class Parcel(BaseModel):
    parcel_id: str
    county_code_dor: str | None = None
    use_code: str | None = None
    use_label: str | None = None
    public_owner: Literal["state", "county", "federal", "municipal", "right_of_way"] | None = None
    owner_name: str | None = None
    # Id de la fuente que dio la parcela: FDACS o el respaldo del condado (PEN-30).
    source: str = "fdacs_parcels"


class Jurisdiction(BaseModel):
    authority: Literal[
        "FDOT", "COUNTY", "CITY", "TOWN", "VILLAGE", "PRIVATE", "SPECIAL_DISTRICT", "UNKNOWN"
    ]
    name: str | None = None
    basis: str
    confidence: Literal["high", "medium", "low"]
    note: str


class SourceStatus(BaseModel):
    id: str
    status: Literal["ok", "error", "timeout"]
    ms: float


class MapPoint(BaseModel):
    lat: float
    lon: float
    roads: list[RoadMatch]
    location: MapLocation
    parcel: Parcel | None = None
    jurisdiction: Jurisdiction
    sources: list[SourceStatus]
    warnings: list[str]


class OspRow(BaseModel):
    county: str | None = None
    state_road_id: str
    section_number: str | None = None
    beginning_milepost: float
    ending_milepost: float


class MapSegment(BaseModel):
    start: MapPoint
    end: MapPoint
    road: RoadMatch
    begin_milepost: float
    end_milepost: float
    length_mi: float
    geometry: dict[Literal["type", "coordinates"], str | list[list[float]]]
    osp_row: OspRow
    jurisdiction: Jurisdiction
    warnings: list[str]


class WorkLocation(BaseModel):
    """Una fila de la tabla Work Location de OSP, por cada vía que sigue el trazo (PEN-32)."""

    county: str | None = None
    # Como en OSP: la ruta ("SR 953"); el ID de vía si la vía no tiene ruta.
    state_road_id: str
    roadway_id: str
    section_number: str | None = None
    beginning_milepost: float
    ending_milepost: float
    # Según la capa de distritos del FDOT con Turnpike (D8, FTE); None si no se pudo consultar.
    on_turnpike: bool | None = None
    kind: Literal["state", "county", "other"]
    local_name: str | None = None
    length_mi: float | None
    geometry: dict[Literal["type", "coordinates"], str | list[list[float]]]


class TraceAdjustment(BaseModel):
    """Separación de los extremos marcados a las vías LRS elegidas, en metros (PEN-36)."""

    start_m: float | None = None
    end_m: float | None = None


class MapTrace(BaseModel):
    path: list[list[float]]
    # Longitud de la polilínea de entrada, útil para explicar un ajuste de la LRS (PEN-35).
    input_length_mi: float
    # Longitud de las geometrías LRS oficiales de las filas, no de la polilínea de entrada.
    length_mi: float | None
    matched_percent: float
    unmatched_length_mi: float
    alignment: Literal["strict", "adjusted", "ambiguous", "unavailable"] = "strict"
    radius_m: float = 25
    coverage_radius_m: float = 25
    snapped_points: list[list[float]] = []
    adjustment: TraceAdjustment | None = None
    rows: list[WorkLocation]
    sources: list[SourceStatus]
    warnings: list[str]


class ParcelOutline(BaseModel):
    parcel_id: str
    # Contornos [[lon, lat], …] sólo para dibujar; sin propietario ni otros datos del tasador.
    rings: list[list[list[float]]]


class ParcelOutlines(BaseModel):
    source: str
    parcels: list[ParcelOutline]
    # True si la fuente devolvió el máximo pedido: puede faltar alguna parcela en la celda.
    truncated: bool


class SearchResult(BaseModel):
    kind: Literal["coordinates", "address", "street", "milepost", "intersection", "nearest"]
    label: str
    detail: str | None = None
    lat: float
    lon: float
    roadway_id: str | None = None
    milepost: float | None = None
    # Sólo en `nearest`: las calles no se cruzan y este es el punto más cercano entre ambas.
    distance_m: float | None = None


class Bounds(BaseModel):
    west: float
    south: float
    east: float
    north: float


class MapCounty(BaseModel):
    name: str
    code_fdot: str


class MapCity(BaseModel):
    name: str
    bounds: Bounds


class MapArea(BaseModel):
    county: str
    code_fdot: str
    city: str | None = None
    bounds: Bounds
    # Contorno simplificado [[lon, lat], …] del condado o de la ciudad elegida, para dibujarlo.
    outline: list[list[list[float]]]
    # Municipios del condado (CLASSFP C1 cuyo punto interior cae dentro del condado).
    cities: list[MapCity]


class MapSearch(BaseModel):
    query: str
    results: list[SearchResult]
    sources: list[SourceStatus]


class MapSource(BaseModel):
    id: str
    name: str
    provider: str
    url: str
    provides: str
    update_frequency: str
    license_note: str


StreetAuthority = Literal[
    "FDOT", "COUNTY", "CITY", "TOWN", "VILLAGE", "PRIVATE", "SPECIAL_DISTRICT"
]


class StreetLine(BaseModel):
    """Tramo del eje de calles de un condado con quién lo mantiene (PEN-41)."""

    id: str
    name: str | None = None
    # Valor del condado tal cual ("St Johns County", "Private CDD"…).
    maintainer: str
    # Null si el valor no dice quién la mantiene (Proposed, Emergency Access, vacío).
    authority: StreetAuthority | None = None
    authority_name: str | None = None
    gated: bool = False
    paths: list[list[list[float]]]


class StreetLines(BaseModel):
    # Null si la celda no toca ningún condado con fuente propia.
    source: str | None = None
    county: str | None = None
    streets: list[StreetLine]
    truncated: bool = False


class TraceStreet(BaseModel):
    name: str | None = None
    maintainer: str
    authority: StreetAuthority | None = None
    authority_name: str | None = None
    gated: bool = False
    # Longitud del dibujo sobre la calle; `paths`, sus tramos tocados por el trazo.
    length_mi: float
    paths: list[list[list[float]]]


class TraceStreets(BaseModel):
    county: str | None = None
    source: str | None = None
    streets: list[TraceStreet]
    unmatched_length_mi: float
    sources: list[SourceStatus]
    warnings: list[str]
