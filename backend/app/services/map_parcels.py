"""Límites de parcelas para dibujar en el mapa (PEN-33): sólo el ID y el contorno.

El panel pide celdas pequeñas (unos 450 m); el condado del centro de la celda decide la fuente
(Broward y Miami-Dade con su capa propia, el resto FDACS). Una parcela al otro lado de un
límite de condado puede faltar en la celda vecina.
"""

from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.models.map import ParcelOutline, ParcelOutlines
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import COUNTIES, Layer, boundary_layer, parcel_outline_layer
from app.services.gis.transport import GisFailure
from app.services.map_mappers import feature_text
from app.services.map_rules import in_florida

Box = tuple[float, float, float, float]
CELL_MAX_DEGREES = 0.006
# ~0,5 m: no se nota a zoom 18 y baja el peso unas diez veces (verificado en Broward).
SIMPLIFY_DEGREES = 0.000005
LIMIT = 1000


class MapParcelsService:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache

    async def outlines(self, box: Box, *, refresh: bool) -> ParcelOutlines:
        west, south, east, north = box
        if not (0 < east - west <= CELL_MAX_DEGREES and 0 < north - south <= CELL_MAX_DEGREES):
            message = f"La celda debe medir como máximo {CELL_MAX_DEGREES} grados por lado."
            raise AppError("PARCEL_CELL_INVALID", message, 422)
        lat, lon = (south + north) / 2, (west + east) / 2
        if not in_florida(lat, lon):
            raise AppError("COORDINATES_OUT_OF_FLORIDA", "La celda está fuera de Florida.", 422)
        key = "map:parcels:" + ":".join(f"{value:.5f}" for value in box)
        return await self._cache.get_or_load(
            key, lambda: self._load(box, lat, lon), refresh=refresh
        )

    async def _load(self, box: Box, lat: float, lon: float) -> ParcelOutlines:
        layer = parcel_outline_layer(self._settings, await self._county(lat, lon))
        try:
            features, _ = await self._client.query_box(
                layer.path, box, layer.fields, simplify_degrees=SIMPLIFY_DEGREES, limit=LIMIT
            )
        except GisFailure:
            raise AppError("GIS_UNAVAILABLE", "La fuente de parcelas no responde.", 502) from None
        parcels = [
            ParcelOutline(parcel_id=parcel_id, rings=rings)
            for feature in features
            if (parcel_id := feature_text(feature, layer.fields[0])) and (rings := _rings(feature))
        ]
        return ParcelOutlines(source=layer.id, parcels=parcels, truncated=len(features) >= LIMIT)

    async def _county(self, lat: float, lon: float) -> str | None:
        """Código del FDOT del condado; si no se sabe, se usa la fuente estatal."""
        layer = Layer("fdot_counties", boundary_layer(self._settings, COUNTIES), ("CNTYNO",))
        try:
            features, _ = await self._client.query_point(layer, lat, lon, 0)
        except GisFailure:
            return None
        return feature_text(features[0], "CNTYNO") if features else None


def _rings(feature: dict[str, Any]) -> list[list[list[float]]]:
    rings = feature.get("geometry", {}).get("rings", [])
    return [
        [[round(float(point[0]), 6), round(float(point[1]), 6)] for point in ring]
        for ring in rings
        if len(ring) >= 3
    ]
