"""Rutas del mapa: sólo validan la consulta y delegan en MapService."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import ServicesDep
from app.models.map import (
    MapArea,
    MapCounty,
    MapPoint,
    MapSearch,
    MapSegment,
    MapSource,
    MapTrace,
    ParcelOutlines,
)

router = APIRouter()
Latitude = Annotated[float, Query(ge=-90, le=90)]
Longitude = Annotated[float, Query(ge=-180, le=180)]
Radius = Annotated[float, Query(ge=1, le=200)]
SearchText = Annotated[str, Query(min_length=3, max_length=120)]
PlaceName = Annotated[str, Query(min_length=2, max_length=60, examples=["Broward"])]
OptionalPlace = Annotated[str | None, Query(min_length=2, max_length=60)]
TracePath = Annotated[
    str,
    Query(
        min_length=7,
        max_length=4000,
        description="Vértices del trazo: `lat,lon;lat,lon;…` (de 2 a 100).",
        examples=["25.771778,-80.263610;25.776800,-80.263800;25.782147,-80.264005"],
    ),
]


@router.get("/search")
async def map_search(
    services: ServicesDep,
    q: SearchText,
    county: OptionalPlace = None,
    city: OptionalPlace = None,
    refresh: bool = False,
) -> MapSearch:
    """Dirección, calle, cruce (`Las Olas & 3rd Ave`), ruta con milepost (`SR 953 3.5`) o
    coordenadas; con `county` (y `city`) se acota a esa zona y suma las calles locales del Censo."""
    return await services.maps.search(q, county=county, city=city, refresh=refresh)


@router.get("/counties")
async def map_counties(services: ServicesDep) -> list[MapCounty]:
    """Los 67 condados de Florida según el FDOT."""
    return await services.maps.counties()


@router.get("/area")
async def map_area(services: ServicesDep, county: PlaceName, city: OptionalPlace = None) -> MapArea:
    """Límites y contorno del condado o de una de sus ciudades, y los municipios del condado."""
    return await services.maps.area(county, city)


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


@router.get("/trace")
async def map_trace(
    services: ServicesDep,
    path: TracePath,
    radius_m: Radius = 25,
    refresh: bool = False,
) -> MapTrace:
    """Tabla Work Location de OSP para una línea dibujada: una fila por vía que sigue."""
    return await services.maps.trace(path, radius_m, refresh=refresh)


@router.get("/parcels")
async def map_parcels(
    services: ServicesDep,
    west: Longitude,
    south: Latitude,
    east: Longitude,
    north: Latitude,
    refresh: bool = False,
) -> ParcelOutlines:
    """Contornos de parcelas de una celda pequeña, sólo con su ID (sin propietarios)."""
    return await services.maps.parcel_outlines((west, south, east, north), refresh=refresh)


@router.get("/sources")
async def map_sources(services: ServicesDep) -> list[MapSource]:
    """Catálogo fijo de fuentes; no llama a proveedores externos."""
    return services.maps.sources()
