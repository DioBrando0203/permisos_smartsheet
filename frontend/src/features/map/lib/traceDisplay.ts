import type { MapTrace } from '../types'
import type { Coordinates } from './coordinates'

export type TraceBounds = { west: number; south: number; east: number; north: number }

export function needsTraceReview(trace: MapTrace): boolean {
  return (
    trace.rows.length === 0 ||
    trace.alignment === 'unavailable' ||
    trace.alignment === 'ambiguous' ||
    trace.warnings.some((warning) => warning === 'TRACE_PARTIAL' || warning === 'TRACE_GEOMETRY_INCOMPLETE')
  )
}

/** Geometrías LRS que se muestran al terminar; el dibujo manual sólo sirve durante la edición. */
export function officialLines(trace: MapTrace): [number, number][][] {
  return trace.rows.map((row) => row.coordinates).filter((coordinates) => coordinates.length > 1)
}

/** Rectángulo de todas las filas para que un enlace de trazo no deje el final fuera de pantalla. */
export function officialBounds(trace: MapTrace, reference: Coordinates[] = []): TraceBounds | null {
  const coordinates = [
    ...officialLines(trace).flat(),
    ...reference.map(({ lat, lon }): [number, number] => [lon, lat]),
  ]
  if (!coordinates.length) return null
  const lons = coordinates.map(([lon]) => lon)
  const lats = coordinates.map(([, lat]) => lat)
  return {
    west: Math.min(...lons),
    south: Math.min(...lats),
    east: Math.max(...lons),
    north: Math.max(...lats),
  }
}
