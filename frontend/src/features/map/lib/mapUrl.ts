import { pointKey, type Coordinates } from './coordinates'

export type MapMode = 'point' | 'trace'
export type TraceOptions = { snap: boolean; original: boolean }

function point(value: string | null): Coordinates | null {
  if (!value) return null
  const [lat, lon] = value.split(',').map(Number)
  return Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null
}

function trace(value: string | null): Coordinates[] | null {
  const points = (value ?? '').split(';').map(point)
  return points.length >= 2 && points.every(Boolean) ? (points as Coordinates[]) : null
}

/** `?p=lat,lon` (punto) o `?t=lat,lon;lat,lon;…` (trazo); `?a=&b=` del antiguo Tramo es un trazo. */
export function readMapUrl(params: URLSearchParams): {
  point: Coordinates | null
  trace: Coordinates[] | null
  options: TraceOptions
} {
  const a = point(params.get('a'))
  const b = point(params.get('b'))
  return {
    point: point(params.get('p')),
    trace: trace(params.get('t')) ?? (a && b ? [a, b] : null),
    options: { snap: params.get('snap') !== 'off', original: params.get('original') === 'on' },
  }
}

export function writeMapUrl(
  mode: MapMode,
  a: Coordinates | null,
  path: Coordinates[] | null,
  options: TraceOptions = { snap: true, original: false },
): URLSearchParams {
  const params = new URLSearchParams()
  if (mode === 'point' && a) params.set('p', pointKey(a))
  if (mode === 'trace' && path) params.set('t', pathKey(path))
  if (mode === 'trace' && !options.snap) params.set('snap', 'off')
  if (mode === 'trace' && options.original) params.set('original', 'on')
  return params
}

export function pathKey(path: Coordinates[]): string {
  return path.map(pointKey).join(';')
}
