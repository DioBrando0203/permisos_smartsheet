"""Rutas del mapa: sólo validan la consulta y delegan en MapService."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ServicesDep
from app.models.map import MapPoint, MapSegment, MapSource

router = APIRouter()
Latitude = Annotated[float, Query(ge=-90, le=90)]
Longitude = Annotated[float, Query(ge=-180, le=180)]
Radius = Annotated[float, Query(ge=1, le=200)]


@router.get("/point")
async def map_point(
    services: ServicesDep,
    lat: Latitude,
    lon: Longitude,
    radius_m: Radius = 25,
    refresh: bool = False,
) -> MapPoint:
    """Vía, milepost, jurisdicción y parcela de un punto de Florida."""
    return await services.maps.point(lat, lon, radius_m, refresh=refresh)


@router.get("/segment")
async def map_segment(
    services: ServicesDep,
    start_lat: Latitude,
    start_lon: Longitude,
    end_lat: Latitude,
    end_lon: Longitude,
    radius_m: Radius = 25,
    refresh: bool = False,
) -> MapSegment:
    """Tramo en una vía común, con la fila lista para OSP."""
    return await services.maps.segment(
        start_lat, start_lon, end_lat, end_lon, radius_m, refresh=refresh
    )


@router.get("/sources")
async def map_sources(services: ServicesDep) -> list[MapSource]:
    """Catálogo fijo de fuentes; no llama a proveedores externos."""
    return services.maps.sources()
