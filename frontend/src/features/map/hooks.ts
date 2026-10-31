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

const staleTime = 10 * 60 * 1000

export function useMapPoint(point: Coordinates | null, refresh = false) {
  return useQuery({
    queryKey: point ? queryKeys.mapPoint(point.lat, point.lon) : ['map-point', 'empty'],
    queryFn: () =>
      api<ApiMapPoint>(
        `/api/map/point?lat=${point!.lat}&lon=${point!.lon}${refresh ? '&refresh=true' : ''}`,
      ).then(normalizeMapPoint),
    enabled: Boolean(point),
    staleTime,
  })
}

/** Tabla Work Location del trazo terminado (PEN-32); `path` es null mientras se dibuja. */
export function useMapTrace(path: Coordinates[] | null) {
  const key = path ? pathKey(path) : ''
  return useQuery({
    queryKey: queryKeys.mapTrace(key),
    queryFn: () => api<ApiMapTrace>(`/api/map/trace?path=${encodeURIComponent(key)}`).then(normalizeMapTrace),
    enabled: Boolean(path),
    staleTime,
  })
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

/** Sugerencias del buscador; `text` ya llega con espera aplicada (MapSearchBox). */
export function useMapSearch(text: string) {
  const query = text.trim()
  return useQuery({
    queryKey: queryKeys.mapSearch(query.toUpperCase()),
    queryFn: () =>
      api<ApiMapSearch>(`/api/map/search?q=${encodeURIComponent(query)}`).then(normalizeMapSearch),
    enabled: query.length >= 3,
    staleTime,
  })
}
