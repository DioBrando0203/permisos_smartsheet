import { useQueries, useQuery, type UseQueryResult } from '@tanstack/react-query'
import { api } from '../../lib/api'
import {
  normalizeMapPoint,
  normalizeMapSearch,
  normalizeMapTrace,
  normalizeParcelOutlines,
} from './normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiMapPoint, ApiMapSearch, ApiMapTrace, ApiParcelOutlines, ParcelOutlines } from './types'
import type { Coordinates } from './lib/coordinates'
import type { Bounds } from './lib/cells'
import { pathKey } from './lib/mapUrl'
import { useMapReading } from './useMapReading'
import {
  normalizeArea,
  normalizeCounties,
  scopeQuery,
  type ApiMapArea,
  type ApiMapCounty,
  type MapScope,
} from './area'

const staleTime = 10 * 60 * 1000

export function useMapPoint(point: Coordinates | null) {
  return useMapReading<ApiMapPoint, ReturnType<typeof normalizeMapPoint>>(
    queryKeys.mapPoint(point?.lat ?? 0, point?.lon ?? 0),
    point ? `/api/map/point?lat=${point.lat}&lon=${point.lon}` : null,
    normalizeMapPoint,
  )
}

/** Tabla Work Location del trazo terminado (PEN-32); `path` es null mientras se dibuja. */
export function useMapTrace(path: Coordinates[] | null) {
  const key = path ? pathKey(path) : ''
  return useMapReading<ApiMapTrace, ReturnType<typeof normalizeMapTrace>>(
    queryKeys.mapTrace(key),
    path ? `/api/map/trace?path=${encodeURIComponent(key)}` : null,
    normalizeMapTrace,
  )
}

export type ParcelLayer = {
  rings: [number, number][][]
  loading: boolean
  failed: number
  truncated: boolean
}

/** Une las celdas sin repetir parcelas (una parcela grande toca varias celdas). */
function combineParcels(results: UseQueryResult<ParcelOutlines>[]): ParcelLayer {
  const seen = new Set<string>()
  const layer: ParcelLayer = { rings: [], loading: false, failed: 0, truncated: false }
  for (const result of results) {
    layer.loading ||= result.isLoading
    layer.failed += result.isError ? 1 : 0
    layer.truncated ||= Boolean(result.data?.truncated)
    for (const parcel of result.data?.parcels ?? []) {
      if (seen.has(parcel.parcelId)) continue
      seen.add(parcel.parcelId)
      layer.rings.push(...parcel.rings)
    }
  }
  return layer
}

/** Contornos de parcelas por celda (PEN-33); cada celda se cachea sola al mover el mapa. */
export function useParcelOutlines(cells: Bounds[]): ParcelLayer {
  return useQueries({
    combine: combineParcels,
    queries: cells.map((cell) => {
      const query = `west=${cell.west}&south=${cell.south}&east=${cell.east}&north=${cell.north}`
      return {
        queryKey: queryKeys.mapParcels(query),
        queryFn: () => api<ApiParcelOutlines>(`/api/map/parcels?${query}`).then(normalizeParcelOutlines),
        staleTime,
      }
    }),
  })
}

/** Sugerencias del buscador, acotadas a la zona; `text` ya llega con espera (MapSearchBox). */
export function useMapSearch(text: string, scope: MapScope) {
  const query = text.trim()
  const zone = scopeQuery(scope)
  return useQuery({
    queryKey: queryKeys.mapSearch(query.toUpperCase(), zone),
    queryFn: () =>
      api<ApiMapSearch>(`/api/map/search?q=${encodeURIComponent(query)}${zone}`).then(normalizeMapSearch),
    enabled: query.length >= 3,
    staleTime,
  })
}

/** Los 67 condados de Florida (cambian casi nunca: se piden una vez por sesión). */
export function useMapCounties() {
  return useQuery({
    queryKey: queryKeys.mapCounties(),
    queryFn: () => api<ApiMapCounty[]>('/api/map/counties').then(normalizeCounties),
    staleTime: Infinity,
  })
}

/** Contorno y límites del condado o de la ciudad, y los municipios del condado. */
export function useMapArea(scope: MapScope) {
  return useQuery({
    queryKey: queryKeys.mapArea(scope.county ?? '', scope.city ?? ''),
    queryFn: () => api<ApiMapArea>(`/api/map/area?${scopeQuery(scope).slice(1)}`).then(normalizeArea),
    enabled: Boolean(scope.county),
    staleTime,
  })
}
