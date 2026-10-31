"""GIS falso: imita las consultas ArcGIS del FDOT y de FDACS y el geocodificador del Censo.

Sirve para E2E sin depender de servicios públicos (ADR-10 del frontend). El backend se apunta
con `GIS_FDOT_BASE_URL=http://127.0.0.1:<puerto>/arcgis/rest/services`,
`GIS_FDACS_PARCELS_URL=http://127.0.0.1:<puerto>/fdacs/parcels/0` y
`GIS_CENSUS_GEOCODER_URL=http://127.0.0.1:<puerto>/census/onelineaddress` (y las parcelas de
Broward en `/broward/parcels/0` y de Miami-Dade en `/miami-dade/parcels/26`). Las capas de vías
aceptan punto con radio, rectángulo (trazo) y `where`. Anota la ruta de cada solicitud y si
llevaba `Authorization` (`GET /_fake/calls`), nunca su contenido.

Uso manual: `python -m tests.fake_gis --port 8792` desde `backend/`.
"""

import argparse
import math
import re
from typing import Any

from fastapi import FastAPI, Request

from tests import fake_gis_data as data

Json = dict[str, Any]
# ArcGIS responde 200 con un objeto `error` cuando no entiende la consulta.
_ARCGIS_ERROR: Json = {"error": {"code": 400, "message": "Unable to complete operation."}}
_LIKE = re.compile(r"^UPPER\(NAME\) LIKE '%([^']+)%'$")
_EQUALS = re.compile(r"^(ROUTENUM|ROADWAY) = '([^']+)'$")
_IN = re.compile(r"^ROADWAY IN \(('[0-9]+'(?:,'[0-9]+')*)\)$")


def create_fake_gis() -> FastAPI:
    app = FastAPI(title="GIS falso")
    calls: list[Json] = []
    app.state.calls = calls

    @app.middleware("http")
    async def record(request: Request, call_next):
        if not request.url.path.startswith("/_fake"):
            calls.append(
                {"path": request.url.path, "authorization": "authorization" in request.headers}
            )
        return await call_next(request)

    @app.get("/arcgis/rest/services/RCI_Layers/MapServer/{layer}/query")
    async def roads(layer: int, request: Request) -> Json:
        return _query_lines(data.ROADS.get(layer, []), dict(request.query_params))

    @app.get("/arcgis/rest/services/Admin_Boundaries/MapServer/{layer}/query")
    async def boundaries(layer: int, request: Request) -> Json:
        return _query_polygon(data.BOUNDARIES.get(layer), dict(request.query_params))

    @app.get("/fdacs/parcels/0/query")
    async def parcels(request: Request) -> Json:
        params = dict(request.query_params)
        lat, lon = _point(params)
        on_road = _meters_to([data.ROUTE], lat, lon) <= data.ROAD_PARCEL_METERS
        return _query_polygon(data.ROAD_GAP if on_road else data.PARCEL, params)

    @app.get("/broward/parcels/0/query")
    async def broward_parcels(request: Request) -> Json:
        return _query_polygon(data.BROWARD_PARCEL, dict(request.query_params))

    @app.get("/miami-dade/parcels/26/query")
    async def miami_dade_parcels(request: Request) -> Json:
        params = dict(request.query_params)
        box = _box(params["geometry"])
        lots = [lot for lot in data.MIAMI_DADE_LOTS if _overlaps(lot["rings"], box)]
        return {
            "features": [
                {"attributes": lot["attributes"], "geometry": {"rings": lot["rings"]}}
                for lot in lots
            ]
        }

    @app.get("/census/onelineaddress")
    async def geocoder(address: str) -> Json:
        matches = [data.ADDRESS] if "42" in address else []
        return {"result": {"input": {"address": {"address": address}}, "addressMatches": matches}}

    @app.get("/_fake/calls")
    async def list_calls() -> list[Json]:
        return calls

    @app.post("/_fake/reset")
    async def reset() -> Json:
        calls.clear()
        return {"ok": True}

    return app


def _query_lines(features: list[Json], params: dict[str, str]) -> Json:
    if "where" in params:
        selected = _where(features, params["where"])
        if selected is None:
            return _ARCGIS_ERROR
    elif params.get("geometryType") == "esriGeometryEnvelope":
        box = _box(params["geometry"])
        selected = [item for item in features if _overlaps(item["paths"], box)]
    else:
        lat, lon = _point(params)
        radius = float(params.get("distance", "0"))
        selected = [item for item in features if _meters_to(item["paths"], lat, lon) <= radius]
    limit = int(params.get("resultRecordCount", "1000"))
    return {"features": [_shape(item, params) for item in selected[:limit]]}


def _query_polygon(attributes: Json | None, params: dict[str, str]) -> Json:
    """Igual que FDOT y FDACS: con `distance` en un polígono la respuesta llega vacía."""
    if attributes is None or "distance" in params:
        return {"features": []}
    return {"features": [_shape({"attributes": attributes}, params)]}


def _where(features: list[Json], where: str) -> list[Json] | None:
    """Sólo las formas que arma `map_query`; cualquier otra es un error de ArcGIS."""
    if match := _LIKE.match(where):
        return [f for f in features if match[1] in str(f["attributes"].get("NAME", "")).upper()]
    if match := _EQUALS.match(where):
        return [f for f in features if str(f["attributes"].get(match[1])) == match[2]]
    if match := _IN.match(where):
        wanted = set(re.findall(r"[0-9]+", match[1]))
        return [f for f in features if f["attributes"].get("ROADWAY") in wanted]
    return None


def _shape(feature: Json, params: dict[str, str]) -> Json:
    """Sólo los campos pedidos, y geometría o medida M sólo si se pidieron."""
    fields = params.get("outFields", "*")
    attributes = feature["attributes"]
    if fields != "*":
        attributes = {name: attributes[name] for name in fields.split(",") if name in attributes}
    shaped: Json = {"attributes": attributes}
    if params.get("returnGeometry") == "true" and feature.get("paths"):
        size = 3 if params.get("returnM") == "true" else 2
        shaped["geometry"] = {"paths": [[p[:size] for p in path] for path in feature["paths"]]}
    return shaped


def _point(params: dict[str, str]) -> tuple[float, float]:
    lon, lat = (float(value) for value in params["geometry"].split(","))
    return lat, lon


def _box(text: str) -> tuple[float, float, float, float]:
    west, south, east, north = (float(value) for value in text.split(","))
    return west, south, east, north


def _overlaps(lines: list[list[list[float]]], box: tuple[float, float, float, float]) -> bool:
    """Algún tramo cuyo rectángulo se cruza con el pedido (basta para datos sintéticos)."""
    west, south, east, north = box
    for line in lines:
        for first, second in zip(line, line[1:], strict=False):
            low_x, high_x = sorted((first[0], second[0]))
            low_y, high_y = sorted((first[1], second[1]))
            if low_x <= east and high_x >= west and low_y <= north and high_y >= south:
                return True
    return False


def _meters_to(paths: list[list[list[float]]], lat: float, lon: float) -> float:
    """Distancia en metros del punto a la polilínea más cercana (plano local, basta en E2E)."""
    scale_x, scale_y = math.cos(math.radians(lat)) * 111_320, 110_540
    best = math.inf
    for path in paths:
        for first, second in zip(path, path[1:], strict=False):
            ax, ay = (first[0] - lon) * scale_x, (first[1] - lat) * scale_y
            dx, dy = (second[0] - first[0]) * scale_x, (second[1] - first[1]) * scale_y
            length = dx * dx + dy * dy
            ratio = max(0.0, min(1.0, -(ax * dx + ay * dy) / length)) if length else 0.0
            best = min(best, math.hypot(ax + ratio * dx, ay + ratio * dy))
    return best


app = create_fake_gis()


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="GIS falso con datos sintéticos")
    parser.add_argument("--port", type=int, default=8792)
    uvicorn.run(app, host="127.0.0.1", port=parser.parse_args().port)
