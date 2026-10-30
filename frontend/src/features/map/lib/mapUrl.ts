import type { Coordinates } from './coordinates'

function point(value: string | null): Coordinates | null {
  if (!value) return null
  const [lat, lon] = value.split(',').map(Number)
  return Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null
}

export function readMapUrl(params: URLSearchParams): {
  point: Coordinates | null
  a: Coordinates | null
  b: Coordinates | null
} {
  return { point: point(params.get('p')), a: point(params.get('a')), b: point(params.get('b')) }
}

export function writeMapUrl(
  mode: 'point' | 'segment',
  a: Coordinates | null,
  b: Coordinates | null,
): URLSearchParams {
  const params = new URLSearchParams()
  const encode = (value: Coordinates) => `${value.lat.toFixed(6)},${value.lon.toFixed(6)}`
  if (mode === 'point' && a) params.set('p', encode(a))
  if (mode === 'segment' && a) params.set('a', encode(a))
  if (mode === 'segment' && b) params.set('b', encode(b))
  return params
}
