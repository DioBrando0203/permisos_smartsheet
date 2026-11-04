/** Tabla única de quién mantiene una calle: color, etiqueta y qué permiso pedir (PEN-41). */
export type StreetTone = 'state' | 'county' | 'city' | 'town' | 'village' | 'private' | 'district' | 'other'

const tones: Record<string, StreetTone> = {
  FDOT: 'state',
  COUNTY: 'county',
  CITY: 'city',
  TOWN: 'town',
  VILLAGE: 'village',
  PRIVATE: 'private',
  SPECIAL_DISTRICT: 'district',
}

/** Orden de la leyenda y texto de cada color: Estado, condado y cada tipo de municipio. */
export const toneLabels: Record<StreetTone, string> = {
  state: 'Estado (FDOT)',
  county: 'County (condado)',
  city: 'City (ciudad)',
  town: 'Town',
  village: 'Village',
  private: 'Privada',
  district: 'CDD',
  other: 'Sin dueño claro',
}

export function streetTone(authority: string | null): StreetTone {
  return tones[authority ?? ''] ?? 'other'
}

/** Clases de una línea o de su muestra en la leyenda: el tono define el color. */
export const toneClass = (tone: StreetTone) => `street-tone--${tone}`

/**
 * Qué permiso corresponde según quién mantiene la calle. Es una guía: cada entidad decide, y el
 * texto lo dice en el panel. Sin autoridad conocida no se sugiere nada (UX-31).
 */
export function permitGuide(authority: string | null, name: string | null): string | null {
  switch (authority) {
    case 'FDOT':
      return 'Permiso del FDOT en OSP.'
    case 'COUNTY':
      return `Permiso de uso del derecho de vía de ${name ?? 'el condado'}.`
    case 'CITY':
    case 'TOWN':
    case 'VILLAGE':
      return `Permiso de derecho de vía de ${name ?? 'el municipio'}.`
    case 'PRIVATE':
      return 'Autorización del dueño o de la asociación (HOA): no es derecho de vía público.'
    case 'SPECIAL_DISTRICT':
      return 'Autorización del distrito (CDD) que mantiene la calle.'
    default:
      return null
  }
}

/** Texto al pasar el cursor por una calle de la capa. */
export function streetTooltip(street: {
  name: string | null
  maintainer: string
  authority: string | null
  gated: boolean
}): string {
  const owner = street.authority ? toneLabels[streetTone(street.authority)] : 'Sin dueño claro'
  const gated = street.gated ? ' · con portón' : ''
  return `${street.name ?? 'Calle sin nombre'} · ${owner} (${street.maintainer || 'sin dato'})${gated}`
}

type ListedStreet = {
  name: string | null
  maintainer: string
  authority: string | null
  authorityName: string | null
  lengthMi: number
}

/** Columnas de "Copiar lista" de las calles del trazo, para Excel o Smartsheet. */
export const streetHeaders = ['Calle', 'Mantenimiento', 'Responsable', 'Longitud (mi)', 'Permiso']

/** Tabla con encabezados, separada por tabulaciones, como la de Work Location. */
export function streetsTableText(streets: ListedStreet[]): string {
  const rows = streets.map((street) => [
    street.name ?? '',
    street.maintainer,
    `${toneLabels[streetTone(street.authority)]}${street.authorityName ? `: ${street.authorityName}` : ''}`,
    street.lengthMi.toFixed(3),
    permitGuide(street.authority, street.authorityName) ?? '',
  ])
  return [streetHeaders, ...rows].map((cells) => cells.join('\t')).join('\n')
}
