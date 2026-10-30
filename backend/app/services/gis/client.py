"""Gateway tipado mínimo para consultas por punto a capas ArcGIS públicas."""

from typing import Any

import httpx

from app.core.config import Settings
from app.services.gis.layers import Layer
from app.services.gis.transport import GisTransport


class GisClient:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self._transport = GisTransport(settings, http)

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
            "distance": str(radius_m) if "roads" in layer.id or layer.id == "fdot_lrs" else "0",
            "units": "esriSRUnit_Meter",
        }
        if layer.with_route:
            params["returnM"] = "true"
        data, elapsed = await self._transport.get(f"{layer.path}/query", params)
        features = data.get("features", [])
        return (features if isinstance(features, list) else []), elapsed
