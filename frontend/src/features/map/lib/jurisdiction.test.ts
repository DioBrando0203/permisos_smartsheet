import { describe, expect, it } from 'vitest'
import { permitGuide, streetsTableText, streetTone, streetTooltip, toneLabels } from './jurisdiction'

describe('Jurisdicción de calles (PEN-41)', () => {
  it('cada autoridad tiene su color: Estado, condado, city, town, village, privada y CDD', () => {
    const authorities = ['FDOT', 'COUNTY', 'CITY', 'TOWN', 'VILLAGE', 'PRIVATE', 'SPECIAL_DISTRICT']
    expect(authorities.map(streetTone)).toEqual([
      'state',
      'county',
      'city',
      'town',
      'village',
      'private',
      'district',
    ])
    expect(streetTone(null)).toBe('other')
    expect(streetTone('UNKNOWN')).toBe('other')
    expect(toneLabels.village).toBe('Village')
  })

  it('sugiere el permiso según quién mantiene la calle y nada si no se sabe', () => {
    expect(permitGuide('FDOT', 'FDOT')).toBe('Permiso del FDOT en OSP.')
    expect(permitGuide('COUNTY', 'St. Johns County')).toBe(
      'Permiso de uso del derecho de vía de St. Johns County.',
    )
    expect(permitGuide('TOWN', 'Town of Jupiter')).toBe('Permiso de derecho de vía de Town of Jupiter.')
    expect(permitGuide('PRIVATE', 'Privada')).toMatch(/no es derecho de vía público/)
    expect(permitGuide('SPECIAL_DISTRICT', null)).toMatch(/CDD/)
    expect(permitGuide('UNKNOWN', null)).toBeNull()
    expect(permitGuide(null, null)).toBeNull()
  })

  it('la lista del trazo se copia con encabezados y el texto al pasar dice el responsable', () => {
    const street = {
      name: 'County Road 210 W',
      maintainer: 'St Johns County',
      authority: 'COUNTY',
      authorityName: 'St. Johns County',
      lengthMi: 0.4761,
      gated: true,
    }
    expect(streetsTableText([street]).split('\n')).toEqual([
      'Calle\tMantenimiento\tResponsable\tLongitud (mi)\tPermiso',
      'County Road 210 W\tSt Johns County\tCounty (condado): St. Johns County\t0.476\tPermiso de uso del derecho de vía de St. Johns County.',
    ])
    expect(streetTooltip(street)).toBe('County Road 210 W · County (condado) (St Johns County) · con portón')
  })
})
