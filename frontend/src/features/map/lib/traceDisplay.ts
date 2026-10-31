import type { MapTrace } from '../types'

export type TraceBounds = { west: number; south: number; east: number; north: number }

/** Geometrías LRS que se muestran al terminar; el dibujo manual sólo sirve durante la edición. */
export function officialLines(trace: MapTrace): [number, number][][] {
  return trace.rows.map((row) => row.coordinates).filter((coordinates) => coordinates.length > 1)
}

/** Rectángulo de todas las filas para que un enlace de trazo no deje el final fuera de pantalla. */
export function officialBounds(trace: MapTrace): TraceBounds | null {
  const coordinates = officialLines(trace).flat()
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
