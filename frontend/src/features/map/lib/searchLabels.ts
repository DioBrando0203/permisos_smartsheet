import {
  Home20Regular,
  Location20Regular,
  Pin20Regular,
  Road20Regular,
  Ruler20Regular,
} from '@fluentui/react-icons'
import type { MapSearchResult } from '../types'

type Kind = MapSearchResult['kind']

export const kindIcons: Record<Kind, typeof Home20Regular> = {
  address: Home20Regular,
  street: Road20Regular,
  milepost: Ruler20Regular,
  coordinates: Location20Regular,
  intersection: Pin20Regular,
  nearest: Pin20Regular,
}
export const kindLabels: Record<Kind, string> = {
  address: 'Dirección',
  street: 'Calle',
  milepost: 'Ruta y milepost',
  coordinates: 'Coordenadas',
  intersection: 'Cruce',
  nearest: 'Punto más cercano',
}
export const searchSourceNames: Record<string, string> = {
  census_geocoder: 'direcciones y cruces (Censo)',
  fdot_streets: 'calles (FDOT)',
  fdot_milepost: 'mileposts (FDOT)',
  fdot_crossings: 'cruces (FDOT)',
  tiger_streets: 'calles locales (Censo)',
  tiger_crossings: 'cruces de calles locales (Censo)',
}
export const searchExamples =
  'Prueba con una dirección (200 E Las Olas Blvd), una calle (Las Olas), un cruce (Las Olas & 3rd Ave) o una ruta con milepost (SR 953 3.5).'

/** Calle y cruce opcional en un solo texto, como lo entiende `/api/map/search`. */
export function searchText(street: string, crossing: string): string {
  const first = street.trim()
  const second = crossing.trim()
  return second ? `${first} & ${second}` : first
}
