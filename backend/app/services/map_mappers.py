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
        feature_text(feature, "ROADWAY"): feature
        for feature in data.get("fdot_lrs", [])
        if feature_text(feature, "ROADWAY")
    }
    states = {feature_text(feature, "ROADWAY") for feature in data.get("fdot_state_roads", [])}
    counties = {feature_text(feature, "ROADWAY") for feature in data.get("fdot_county_roads", [])}
    names: dict[str, list[dict[str, Any]]] = {}
    for feature in data.get("fdot_local_names", []):
        names.setdefault(feature_text(feature, "ROADWAY"), []).append(feature)
    roads: list[RoadMatch] = []
    routes: dict[str, RouteGeometry] = {}
    for roadway, feature in lrs.items():
        route = route_geometry(feature, roadway)
        if route:
            routes[roadway] = route
        attrs = _attributes(feature)
        kind = "state" if roadway in states else "county" if roadway in counties else "other"
        milepost = milepost_at(lat, lon, route) if route else to_number(attrs.get("BEGIN_POST"))
        roads.append(
            RoadMatch(
                roadway_id=roadway,
                county_code_fdot=feature_text(feature, "COUNTY"),
                section=_section(feature_text(feature, "SECTION")),
                subsection=roadway[-3:] if len(roadway) >= 3 else None,
                kind=kind,
                route=_route_name(data, roadway),
                local_name=_local_name(names.get(roadway, []), milepost),
                milepost=milepost,
                distance_m=_distance(attrs, route, lat, lon),
                begin_post=to_number(attrs.get("BEGIN_POST")),
                end_post=to_number(attrs.get("END_POST")),
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
        # FDACS entrega CO_NO como número (23.0); el código del DOR es entero.
        county_code_dor=_string(int(code) if (code := to_number(attrs.get("CO_NO"))) else None),
        use_code=use_code,
        use_label=use[0] if use else None,
        public_owner=use[1] if use else None,
        owner_name=_string(attrs.get("OWN_NAME")),
    ), None


def build_county_parcel(
    features: list[dict[str, Any]], *, county_code_dor: str, source: str
) -> Parcel | None:
    """Respaldo de un condado: sólo el ID (folio); uso y propietario quedan desconocidos."""
    parcel_id = _string(_attributes(_first(features)).get("FOLIO"))
    if not parcel_id:
        return None
    return Parcel(parcel_id=parcel_id, county_code_dor=county_code_dor, source=source)


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


def _local_name(features: list[dict[str, Any]], milepost: float | None) -> str | None:
    """Una vía cambia de nombre por tramos (SW 42 Ave, NW 42 Ave): gana el que contiene el MP."""
    for feature in features:
        attrs = _attributes(feature)
        begin, end = to_number(attrs.get("BEGIN_POST")), to_number(attrs.get("END_POST"))
        if milepost is not None and begin is not None and end is not None:
            if begin <= milepost <= end:
                return feature_text(feature, "NAME") or None
    if not features:
        return None
    return feature_text(features[0], "NAME") or None


def _route_name(data: dict[str, list[dict[str, Any]]], roadway: str) -> str | None:
    for source in ("fdot_state_roads", "fdot_county_roads"):
        for feature in data.get(source, []):
            if feature_text(feature, "ROADWAY") == roadway:
                return normalize_route(_attributes(feature).get("ROUTE"))
    return None


def route_geometry(feature: dict[str, Any], roadway: str) -> RouteGeometry | None:
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


def feature_text(feature: dict[str, Any], field: str) -> str:
    return _string(_attributes(feature).get(field)) or ""


def _first(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    return items[0] if items else None


def _string(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def to_number(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _distance(attrs: dict[str, Any], route: RouteGeometry | None, lat: float, lon: float) -> float:
    supplied = to_number(attrs.get("distance"))
    if supplied and supplied > 0:
        return round(supplied, 1)
    return distance_m_to_route(lat, lon, route) if route else 0.0


def _section(value: str) -> str | None:
    return value[:3] if len(value) == 6 and value.endswith("000") else value or None
