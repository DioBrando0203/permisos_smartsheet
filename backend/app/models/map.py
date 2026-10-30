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
    city: str | None = None
    zip: str | None = None


class Parcel(BaseModel):
    parcel_id: str
    county_code_dor: str | None = None
    use_code: str | None = None
    use_label: str | None = None
    public_owner: Literal["state", "county", "federal", "municipal", "right_of_way"] | None = None
    owner_name: str | None = None


class Jurisdiction(BaseModel):
    authority: Literal["FDOT", "COUNTY", "CITY", "PRIVATE", "SPECIAL_DISTRICT", "UNKNOWN"]
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


class MapSource(BaseModel):
    id: str
    name: str
    provider: str
    url: str
    provides: str
    update_frequency: str
    license_note: str
