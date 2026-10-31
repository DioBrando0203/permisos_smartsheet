"""Caso de uso de mapa: agrega GIS público, caché y contrato seguro del panel."""

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.models.map import (
    MapArea,
    MapCounty,
    MapPoint,
    MapSearch,
    MapSegment,
    MapSource,
    MapTrace,
    OspRow,
    Parcel,
    ParcelOutlines,
    SourceStatus,
)
from app.services.cache import TtlCache
from app.services.gis import GisClient
from app.services.gis.layers import BROWARD_DOR, BROWARD_FDOT, Layer, broward_parcels, layers
from app.services.gis.transport import GisFailure
from app.services.map_mappers import (
    build_county_parcel,
    build_location,
    build_parcel,
    build_roads,
    warnings,
)
from app.services.map_parcels import MapParcelsService
from app.services.map_places import MapPlacesService
from app.services.map_rules import (
    RouteGeometry,
    haversine_miles,
    in_florida,
    jurisdiction,
    pick_segment_road,
    slice_route,
)
from app.services.map_search import MapSearchService
from app.services.map_trace import MapTraceService


@dataclass(frozen=True)
class _Resolution:
    point: MapPoint
    routes: dict[str, RouteGeometry]


class MapService:
    def __init__(self, settings: Settings, client: GisClient, cache: TtlCache) -> None:
        self._settings, self._client, self._cache = settings, client, cache
        self._places = MapPlacesService(settings, client, cache)
        self._search = MapSearchService(settings, client, cache, self._places)
        self._trace = MapTraceService(settings, client, cache)
        self._parcels = MapParcelsService(settings, client, cache)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search(
        self, text: str, *, county: str | None, city: str | None, refresh: bool
    ) -> MapSearch:
        self._ensure_enabled()
        return await self._search.search(text, county=county, city=city, refresh=refresh)

    async def counties(self) -> list[MapCounty]:
        self._ensure_enabled()
        return await self._places.counties()

    async def area(self, county: str, city: str | None) -> MapArea:
        self._ensure_enabled()
        return await self._places.area(county, city)

    async def trace(
        self, path: str, radius_m: float, *, refresh: bool, snap: bool = False
    ) -> MapTrace:
        self._ensure_enabled()
        return await self._trace.trace(path, radius_m, refresh=refresh, snap=snap)

    async def parcel_outlines(
        self, box: tuple[float, float, float, float], *, refresh: bool
    ) -> ParcelOutlines:
        self._ensure_enabled()
        return await self._parcels.outlines(box, refresh=refresh)

    async def point(self, lat: float, lon: float, radius_m: float, *, refresh: bool) -> MapPoint:
        return (await self._resolve(lat, lon, radius_m, refresh=refresh)).point

    async def segment(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        radius_m: float,
        *,
        refresh: bool,
    ) -> MapSegment:
        self._ensure_enabled()
        self._ensure_florida(start_lat, start_lon)
        self._ensure_florida(end_lat, end_lon)
        length = haversine_miles(start_lat, start_lon, end_lat, end_lon)
        if length > self._settings.gis_max_segment_miles:
            raise AppError("SEGMENT_TOO_LONG", "El tramo supera la longitud máxima permitida.", 422)
        start, end = await asyncio.gather(
            self._resolve(start_lat, start_lon, radius_m, refresh=refresh),
            self._resolve(end_lat, end_lon, radius_m, refresh=refresh),
        )
        road = pick_segment_road(start.point.roads, end.point.roads)
        if road is None:
            raise AppError(
                "SEGMENT_ROADWAY_MISMATCH", "Los puntos no están sobre la misma vía.", 422
            )
        end_road = next(item for item in end.point.roads if item.roadway_id == road.roadway_id)
        if road.milepost is None or end_road.milepost is None:
            raise AppError(
                "SEGMENT_ROADWAY_MISMATCH", "La vía no tiene milepost para el tramo.", 422
            )
        begin, finish = sorted((road.milepost, end_road.milepost))
        geometry = slice_route(
            start.routes.get(road.roadway_id, RouteGeometry(road.roadway_id, ())), begin, finish
        )
        if not geometry:
            geometry = [
                [round(start_lon, 6), round(start_lat, 6)],
                [round(end_lon, 6), round(end_lat, 6)],
            ]
        return MapSegment(
            start=start.point,
            end=end.point,
            road=road,
            begin_milepost=begin,
            end_milepost=finish,
            length_mi=round(length, 3),
            geometry={"type": "LineString", "coordinates": geometry},
            osp_row=OspRow(
                county=start.point.location.county,
                # Como OSP: "SR 953", no el ID de vía (PEN-32).
                state_road_id=road.route or road.roadway_id,
                section_number=road.section,
                beginning_milepost=begin,
                ending_milepost=finish,
            ),
            jurisdiction=start.point.jurisdiction,
            warnings=sorted(set(start.point.warnings + end.point.warnings)),
        )

    def sources(self) -> list[MapSource]:
        return [
            MapSource(
                id="fdot_lrs",
                name="LRS Basemap Routes",
                provider="FDOT",
                url="https://gis.fdot.gov/",
                provides="Vía y milepost",
                update_frequency="Según FDOT",
                license_note="Datos públicos.",
            ),
            MapSource(
                id="fdot_boundaries",
                name="Límites administrativos",
                provider="FDOT",
                url="https://gis.fdot.gov/",
                provides="Condado, ciudad y ZIP",
                update_frequency="Según FDOT",
                license_note="Datos públicos.",
            ),
            MapSource(
                id="fdacs_parcels",
                name="Parcelas",
                provider="FDACS",
                url="https://gis.fdacs.gov/",
                provides="Parcela y uso de suelo",
                update_frequency="Según FDACS",
                license_note="Registro público; confirmar con el tasador.",
            ),
            MapSource(
                id="broward_parcels",
                name="Parcelas de Broward (respaldo)",
                provider="Broward County",
                url="https://services.arcgis.com/JMAJrTsHNLrSsWf5/ArcGIS/rest/services/Parcels",
                provides="Folio de la parcela cuando FDACS no responde",
                update_frequency="Según el condado",
                license_note="Datos públicos; condiciones de uso por revisar (MJ-PEN-06).",
            ),
        ]

    async def _resolve(
        self, lat: float, lon: float, radius_m: float, *, refresh: bool
    ) -> _Resolution:
        self._ensure_enabled()
        self._ensure_florida(lat, lon)
        key = f"map:point:{lat:.5f}:{lon:.5f}:{radius_m:.1f}"
        return await self._cache.get_or_load(
            key, lambda: self._load_point(lat, lon, radius_m), refresh=refresh
        )

    async def _load_point(self, lat: float, lon: float, radius_m: float) -> _Resolution:
        results = await asyncio.gather(
            *(self._query(layer, lat, lon, radius_m) for layer in layers(self._settings))
        )
        data, statuses = (
            {source.id: features for source, features, _ in results},
            [status for _, _, status in results],
        )
        if all(status.status != "ok" for status in statuses[:-1]):
            raise AppError("GIS_UNAVAILABLE", "Los servicios GIS no responden.", 502)
        roads, routes = build_roads(data, lat, lon)
        location = build_location(data)
        parcel, parcel_warning = build_parcel(data.get("fdacs_parcels", []))
        if statuses[-1].status != "ok" and location.county_code_fdot == BROWARD_FDOT:
            parcel, fallback = await self._broward_parcel(lat, lon, radius_m)
            statuses.append(fallback)
        point = MapPoint(
            lat=round(lat, 6),
            lon=round(lon, 6),
            roads=roads,
            location=location,
            parcel=parcel,
            jurisdiction=jurisdiction(roads[0] if roads else None, location),
            sources=statuses,
            warnings=warnings(roads, statuses, parcel_warning),
        )
        return _Resolution(point, routes)

    async def _broward_parcel(
        self, lat: float, lon: float, radius_m: float
    ) -> tuple[Parcel | None, SourceStatus]:
        """FDACS falló en Broward: el folio sale de la capa pública del condado (PEN-30)."""
        layer, features, status = await self._query(
            broward_parcels(self._settings), lat, lon, radius_m
        )
        parcel = build_county_parcel(features, county_code_dor=BROWARD_DOR, source=layer.id)
        return parcel, status

    async def _query(
        self, layer: Layer, lat: float, lon: float, radius_m: float
    ) -> tuple[Layer, list[dict[str, Any]], SourceStatus]:
        started = perf_counter()
        try:
            features, elapsed = await self._client.query_point(layer, lat, lon, radius_m)
            return layer, features, SourceStatus(id=layer.id, status="ok", ms=elapsed)
        except GisFailure as error:
            return (
                layer,
                [],
                SourceStatus(
                    id=layer.id, status=error.status, ms=round((perf_counter() - started) * 1000, 1)
                ),
            )

    def _ensure_enabled(self) -> None:
        if not self._settings.app_gis_enabled:
            raise AppError("GIS_DISABLED", "El mapa está deshabilitado en este servidor.", 503)

    @staticmethod
    def _ensure_florida(lat: float, lon: float) -> None:
        if not in_florida(lat, lon):
            raise AppError("COORDINATES_OUT_OF_FLORIDA", "El punto está fuera de Florida.", 422)
