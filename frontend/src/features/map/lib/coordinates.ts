export type Coordinates = { lat: number; lon: number }

export function parseCoordinates(value: string): Coordinates | null {
  const parts = value
    .trim()
    .split(/[\s,]+/)
    .filter(Boolean)
  if (parts.length !== 2) return null
  const [lat, lon] = parts.map(Number)
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180)
    return null
  return { lat, lon }
}

export function pointKey(point: Coordinates): string {
  return `${point.lat.toFixed(6)},${point.lon.toFixed(6)}`
}
