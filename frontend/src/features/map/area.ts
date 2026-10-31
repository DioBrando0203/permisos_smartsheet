import type { Bounds } from './lib/cells'

/** Zona elegida para ubicarse y acotar el buscador; sin condado se busca en todo Florida. */
export type MapScope = { county: string | null; city: string | null }
export type MapCounty = { name: string; codeFdot: string }
export type MapCity = { name: string; bounds: Bounds }
export type MapArea = {
  county: string
  codeFdot: string
  city: string | null
  bounds: Bounds
  outline: [number, number][][]
  cities: MapCity[]
}

type ApiBounds = Partial<Bounds>
export type ApiMapCounty = { name?: string; code_fdot?: string }
export type ApiMapArea = {
  county?: string
  code_fdot?: string
  city?: string | null
  bounds?: ApiBounds
  outline?: [number, number][][]
  cities?: { name?: string; bounds?: ApiBounds }[]
}

/** Condados donde trabaja el equipo: van primero en el selector. */
export const featuredCounties = ['Broward', 'Palm Beach', 'Martin', 'Miami-Dade']

const bounds = (source?: ApiBounds): Bounds => ({
  west: source?.west ?? 0,
  south: source?.south ?? 0,
  east: source?.east ?? 0,
  north: source?.north ?? 0,
})

export function normalizeCounties(source: ApiMapCounty[]): MapCounty[] {
  return source.map((county) => ({ name: county.name ?? '', codeFdot: county.code_fdot ?? '' }))
}

export function normalizeArea(source: ApiMapArea): MapArea {
  return {
    county: source.county ?? '',
    codeFdot: source.code_fdot ?? '',
    city: source.city ?? null,
    bounds: bounds(source.bounds),
    outline: source.outline ?? [],
    cities: (source.cities ?? []).map((city) => ({ name: city.name ?? '', bounds: bounds(city.bounds) })),
  }
}

export function scopeQuery(scope: MapScope): string {
  const params = new URLSearchParams()
  if (scope.county) params.set('county', scope.county)
  if (scope.county && scope.city) params.set('city', scope.city)
  const text = params.toString()
  return text ? `&${text}` : ''
}
