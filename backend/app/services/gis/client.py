"""Gateway tipado mínimo para consultas a capas ArcGIS públicas y al geocodificador del Censo."""

from typing import Any

import httpx

from app.core.config import Settings
from app.services.gis.layers import Layer
from app.services.gis.transport import GisTransport


class GisClient:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._transport = GisTransport(settings, http)
        self._geocoder_url = settings.gis_census_geocoder_url

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def query_point(
        self, layer: Layer, lat: float, lon: float, radius_m: float
    ) -> tuple[list[dict[str, Any]], float]:
        """Consulta una capa, pidiendo sólo campos necesarios y geometría LRS cuando aplica."""
        params = {
            "f": "json",
            "geometry": f"{lon:.6f},{lat:.6f}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": ",".join(layer.fields),
            "returnGeometry": "true" if layer.with_route else "false",
            "outSR": "4326",
        }
        if layer.radius:
            params |= {"distance": str(radius_m), "units": "esriSRUnit_Meter"}
        if layer.with_route:
            params["returnM"] = "true"
        return await self._features(f"{layer.path}/query", params)

    async def query_where(
        self,
        path: str,
        where: str,
        fields: tuple[str, ...],
        *,
        limit: int,
        geometry: bool = True,
        with_m: bool = False,
        box: tuple[float, float, float, float] | None = None,
        simplify_degrees: float | None = None,
    ) -> tuple[list[dict[str, Any]], float]:
        """Búsqueda por atributos, opcionalmente dentro de un rectángulo (oeste, sur, este, norte).

        `where` sólo se arma con texto validado (map_query) o con nombres que dio la propia fuente.
        """
        params = {
            "f": "json",
            "where": where,
            "outFields": ",".join(fields),
            "returnGeometry": "true" if geometry else "false",
            "outSR": "4326",
            "geometryPrecision": "6",
            "resultRecordCount": str(limit),
        }
        if box:
            params |= {
                "geometry": ",".join(f"{value:.6f}" for value in box),
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            }
        if with_m:
            params["returnM"] = "true"
        if simplify_degrees:
            params["maxAllowableOffset"] = f"{simplify_degrees:.7f}"
        return await self._features(f"{path}/query", params)

    async def query_box(
        self,
        path: str,
        box: tuple[float, float, float, float],
        fields: tuple[str, ...],
        *,
        with_m: bool = False,
        simplify_degrees: float | None = None,
        limit: int | None = None,
    ) -> tuple[list[dict[str, Any]], float]:
        """Elementos que tocan el rectángulo (oeste, sur, este, norte), con geometría en WGS84."""
        params = {
            "f": "json",
            "geometry": ",".join(f"{value:.6f}" for value in box),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": ",".join(fields),
            "returnGeometry": "true",
            "outSR": "4326",
            "geometryPrecision": "6",
        }
        if with_m:
            params["returnM"] = "true"
        if simplify_degrees:
            params["maxAllowableOffset"] = f"{simplify_degrees:.7f}"
        if limit:
            params["resultRecordCount"] = str(limit)
        return await self._features(f"{path}/query", params)

    async def geocode(self, address: str) -> tuple[list[dict[str, Any]], float]:
        """Direcciones de EE. UU. con el geocodificador público del Censo (sin clave)."""
        params = {"address": address, "benchmark": "Public_AR_Current", "format": "json"}
        data, elapsed = await self._transport.get(self._geocoder_url, params)
        matches = data.get("result", {}).get("addressMatches", [])
        return (matches if isinstance(matches, list) else []), elapsed

    async def _features(
        self, url: str, params: dict[str, str]
    ) -> tuple[list[dict[str, Any]], float]:
        data, elapsed = await self._transport.get(url, params)
        features = data.get("features", [])
        return (features if isinstance(features, list) else []), elapsed
