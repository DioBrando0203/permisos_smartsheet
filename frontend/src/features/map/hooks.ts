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
  normalizeStreetLines,
  normalizeTraceStreets,
  type ApiStreetLines,
  type ApiTraceStreets,
  type StreetLine,
  type StreetLines,
} from './streets'
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
export function useMapTrace(path: Coordinates[] | null, snap = true) {
  const key = path ? pathKey(path) : ''
  return useMapReading<ApiMapTrace, ReturnType<typeof normalizeMapTrace>>(
    queryKeys.mapTrace(key, snap),
    path ? `/api/map/trace?path=${encodeURIComponent(key)}&snap=${snap}&radius_m=${snap ? 100 : 25}` : null,
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

export type StreetLayer = {
  streets: StreetLine[]
  loading: boolean
  failed: number
  truncated: boolean
  /** Alguna celda tocó un condado con fuente propia (St. Johns). */
  available: boolean
}

/** Une las celdas sin repetir tramos (un tramo largo toca varias celdas). */
function combineStreets(results: UseQueryResult<StreetLines>[]): StreetLayer {
  const seen = new Set<string>()
  const layer: StreetLayer = { streets: [], loading: false, failed: 0, truncated: false, available: false }
  for (const result of results) {
    layer.loading ||= result.isLoading
    layer.failed += result.isError ? 1 : 0
    layer.truncated ||= Boolean(result.data?.truncated)
    layer.available ||= Boolean(result.data?.source)
    for (const street of result.data?.streets ?? []) {
      if (seen.has(street.id)) continue
      seen.add(street.id)
      layer.streets.push(street)
    }
  }
  return layer
}

/** Calles del condado por celda con quién las mantiene (PEN-41), como las parcelas. */
export function useStreetLines(cells: Bounds[]): StreetLayer {
  return useQueries({
    combine: combineStreets,
    queries: cells.map((cell) => {
      const query = `west=${cell.west}&south=${cell.south}&east=${cell.east}&north=${cell.north}`
      return {
        queryKey: queryKeys.mapStreets(query),
        queryFn: () => api<ApiStreetLines>(`/api/map/streets?${query}`).then(normalizeStreetLines),
        staleTime,
      }
    }),
  })
}

/** Calles del condado que sigue el trazo terminado, con su responsable (PEN-41). */
export function useTraceStreets(path: Coordinates[] | null) {
  const key = path ? pathKey(path) : ''
  return useMapReading<ApiTraceStreets, ReturnType<typeof normalizeTraceStreets>>(
    queryKeys.mapTraceStreets(key),
    path ? `/api/map/trace/streets?path=${encodeURIComponent(key)}` : null,
    normalizeTraceStreets,
  )
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
