"""Traduce respuestas ArcGIS a modelos del mapa sin exponer JSON del proveedor."""

from typing import Any

from app.models.map import MapLocation, Parcel, RoadMatch, SourceStatus
from app.services.map_rules import (
    DOR_USES,
    RouteGeometry,
    distance_m_to_route,
    milepost_at,
    normalize_route,
)


def build_roads(
    data: dict[str, list[dict[str, Any]]], lat: float, lon: float
) -> tuple[list[RoadMatch], dict[str, RouteGeometry]]:
    lrs = {
        _value(feature, "ROADWAY"): feature
        for feature in data.get("fdot_lrs", [])
        if _value(feature, "ROADWAY")
    }
    states = {_value(feature, "ROADWAY") for feature in data.get("fdot_state_roads", [])}
    counties = {_value(feature, "ROADWAY") for feature in data.get("fdot_county_roads", [])}
    names = {
        _value(feature, "ROADWAY"): _value(feature, "NAME")
        for feature in data.get("fdot_local_names", [])
    }
    roads: list[RoadMatch] = []
    routes: dict[str, RouteGeometry] = {}
    for roadway, feature in lrs.items():
        route = _route(feature, roadway)
        if route:
            routes[roadway] = route
        attrs = _attributes(feature)
        kind = "state" if roadway in states else "county" if roadway in counties else "other"
        roads.append(
            RoadMatch(
                roadway_id=roadway,
                county_code_fdot=_value(feature, "COUNTY"),
                section=_section(_value(feature, "SECTION")),
                subsection=roadway[-3:] if len(roadway) >= 3 else None,
                kind=kind,
                route=_route_name(data, roadway),
                local_name=names.get(roadway),
                milepost=milepost_at(lat, lon, route)
                if route
                else _number(attrs.get("BEGIN_POST")),
                distance_m=_distance(attrs, route, lat, lon),
                begin_post=_number(attrs.get("BEGIN_POST")),
                end_post=_number(attrs.get("END_POST")),
            )
        )
    roads.sort(key=lambda road: road.distance_m)
    return roads, routes


def build_location(data: dict[str, list[dict[str, Any]]]) -> MapLocation:
    county, city, zip_code = (
        _attributes(_first(data.get(source, [])))
        for source in ("fdot_counties", "fdot_cities", "fdot_zip")
    )
    return MapLocation(
        county=_string(county.get("COUNTY")),
        county_code_fdot=_string(county.get("CNTYNO")),
        fdot_district=_string(county.get("DISTRICT")),
        city=_string(city.get("NAME")),
        zip=_string(zip_code.get("ZIP")),
    )


def build_parcel(features: list[dict[str, Any]]) -> tuple[Parcel | None, str | None]:
    attrs = _attributes(_first(features))
    parcel_id = _string(attrs.get("PARCEL_ID"))
    if not parcel_id:
        return None, "PARCEL_IS_ROAD" if attrs else None
    use_code = _string(attrs.get("DOR_UC"))
    use = DOR_USES.get(use_code or "")
    return Parcel(
        parcel_id=parcel_id,
        county_code_dor=_string(attrs.get("CO_NO")),
        use_code=use_code,
        use_label=use[0] if use else None,
        public_owner=use[1] if use else None,
        owner_name=_string(attrs.get("OWN_NAME")),
    ), None


def warnings(
    roads: list[RoadMatch], statuses: list[SourceStatus], parcel_warning: str | None
) -> list[str]:
    result = ["SOURCE_FAILED"] if any(status.status != "ok" for status in statuses) else []
    if not roads:
        result.append("NO_ROAD_NEARBY")
    if len(roads) > 1:
        result.append("MULTIPLE_ROADS")
    if parcel_warning:
        result.append(parcel_warning)
    return result


def _route_name(data: dict[str, list[dict[str, Any]]], roadway: str) -> str | None:
    for source in ("fdot_state_roads", "fdot_county_roads"):
        for feature in data.get(source, []):
            if _value(feature, "ROADWAY") == roadway:
                return normalize_route(_attributes(feature).get("ROUTE"))
    return None


def _route(feature: dict[str, Any], roadway: str) -> RouteGeometry | None:
    paths = feature.get("geometry", {}).get("paths", [])
    converted = tuple(
        tuple(
            (
                float(point[0]),
                float(point[1]),
                float(point[2]) if len(point) > 2 and point[2] is not None else None,
            )
            for point in path
            if len(point) >= 2
        )
        for path in paths
    )
    return RouteGeometry(roadway, converted) if converted else None


def _attributes(feature: dict[str, Any] | None) -> dict[str, Any]:
    return feature.get("attributes", {}) if feature else {}


def _value(feature: dict[str, Any], field: str) -> str:
    return _string(_attributes(feature).get(field)) or ""


def _first(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    return items[0] if items else None


def _string(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _number(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _distance(attrs: dict[str, Any], route: RouteGeometry | None, lat: float, lon: float) -> float:
    supplied = _number(attrs.get("distance"))
    if supplied and supplied > 0:
        return round(supplied, 1)
    return distance_m_to_route(lat, lon, route) if route else 0.0


def _section(value: str) -> str | None:
    return value[:3] if len(value) == 6 and value.endswith("000") else value or None
