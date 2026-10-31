import { useMemo } from 'react'
import type { MapFocus, MapLine, MapMarker } from '../../components/map/MapView'
import type { Coordinates } from './lib/coordinates'
import type { MapMode } from './lib/mapUrl'
import { needsTraceReview, officialBounds, officialLines } from './lib/traceDisplay'
import type { MapTrace } from './types'

type Drawing = { vertices: Coordinates[]; drawing: boolean }

/** Presentación derivada: los resultados incompletos conservan el dibujo como referencia. */
export function useMapDrawing(mode: MapMode, point: Coordinates | null, trace: Drawing, result?: MapTrace) {
  const review = Boolean(result && needsTraceReview(result))
  const focus = useMemo<MapFocus | null>(() => {
    if (mode !== 'trace' || trace.drawing || !result) return null
    const bounds = officialBounds(result, review ? trace.vertices : [])
    return bounds ? { bounds } : null
  }, [mode, result, review, trace.drawing, trace.vertices])
  const markers = useMemo<MapMarker[]>(() => {
    if (mode === 'point') return point ? [point] : []
    if (!trace.drawing && result && !review) return []
    return trace.vertices.map((vertex, index) => ({
      ...vertex,
      small: true,
      label: index ? undefined : 'Inicio',
    }))
  }, [point, mode, result, review, trace.drawing, trace.vertices])
  const lines = useMemo<MapLine[]>(() => {
    if (mode !== 'trace') return []
    const draft: MapLine = {
      coordinates: trace.vertices.map(({ lat, lon }) => [lon, lat]),
      style: 'draft',
    }
    if (trace.drawing || !result) return [draft]
    const official: MapLine[] = officialLines(result).map((coordinates) => ({ coordinates, style: 'result' }))
    return review ? [draft, ...official] : official
  }, [mode, trace.vertices, trace.drawing, result, review])
  return { focus, markers, lines }
}
