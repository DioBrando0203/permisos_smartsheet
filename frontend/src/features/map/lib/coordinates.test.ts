import { describe, expect, it } from 'vitest'
import { parseCoordinates } from './coordinates'
import { ospText } from './ospRow'

describe('coordenadas del mapa', () => {
  it('acepta coma o espacio y rechaza texto inválido', () => {
    expect(parseCoordinates('25.771778, -80.263610')).toEqual({ lat: 25.771778, lon: -80.26361 })
    expect(parseCoordinates('25.771778 -80.263610')).toEqual({ lat: 25.771778, lon: -80.26361 })
    expect(parseCoordinates('calle')).toBeNull()
  })

  it('arma la fila OSP como cinco columnas tabuladas', () => {
    expect(
      ospText({
        ospRow: {
          county: 'Miami-Dade',
          stateRoadId: '87281000',
          sectionNumber: '281',
          beginningMilepost: 3.124,
          endingMilepost: 3.839,
        },
      } as never),
    ).toBe('Miami-Dade\t87281000\t281\t3.124\t3.839')
  })
})
