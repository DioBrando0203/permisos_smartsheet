import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeMapPoint, normalizeMapSegment } from './normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiMapPoint, ApiMapSegment } from './types'
import type { Coordinates } from './lib/coordinates'

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

export function useMapSegment(a: Coordinates | null, b: Coordinates | null, refresh = false) {
  return useQuery({
    queryKey:
      a && b ? queryKeys.mapSegment(`${a.lat},${a.lon}`, `${b.lat},${b.lon}`) : ['map-segment', 'empty'],
    queryFn: () =>
      api<ApiMapSegment>(
        `/api/map/segment?start_lat=${a!.lat}&start_lon=${a!.lon}&end_lat=${b!.lat}&end_lon=${b!.lon}${refresh ? '&refresh=true' : ''}`,
      ).then(normalizeMapSegment),
    enabled: Boolean(a && b),
    staleTime,
  })
}
