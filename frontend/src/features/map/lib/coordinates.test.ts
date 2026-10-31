import { describe, expect, it } from 'vitest'
import { mapTraceFixture } from '../../../test/fixtures/map'
import { normalizeMapTrace } from '../normalize'
import { cellsFor } from './cells'
import { parseCoordinates } from './coordinates'
import { readMapUrl, writeMapUrl } from './mapUrl'
import { ospRowText, ospTableText } from './ospRow'

describe('coordenadas del mapa', () => {
  it('acepta coma o espacio y rechaza texto inválido', () => {
    expect(parseCoordinates('25.771778, -80.263610')).toEqual({ lat: 25.771778, lon: -80.26361 })
    expect(parseCoordinates('25.771778 -80.263610')).toEqual({ lat: 25.771778, lon: -80.26361 })
    expect(parseCoordinates('calle')).toBeNull()
  })
})

describe('tabla Work Location (PEN-32)', () => {
  const rows = normalizeMapTrace(mapTraceFixture).rows

  it('copia una fila con las columnas de OSP, State Road ID como ruta', () => {
    expect(ospRowText(rows[0])).toBe('Miami-Dade\tSR 953\t281\t3.124\t3.839\tNo')
    expect(ospRowText(rows[1])).toBe('Miami-Dade\t87000442\t000442\t0.100\t0.304\t')
  })

  it('copia la tabla con encabezados para Excel o Smartsheet', () => {
    const lines = ospTableText(rows).split('\n')
    expect(lines[0]).toBe(
      'County\tState Road ID\tSection Number\tBeginning Milepost\tEnding Milepost\tIs Location on Turnpike?',
    )
    expect(lines).toHaveLength(3)
  })
})

describe('URL del mapa', () => {
  it('lee y escribe el trazo, y convierte el antiguo tramo ?a=&b=', () => {
    const path = [
      { lat: 25.771778, lon: -80.26361 },
      { lat: 25.782147, lon: -80.264005 },
    ]
    const written = writeMapUrl('trace', null, path)
    expect(written.get('t')).toBe('25.771778,-80.263610;25.782147,-80.264005')
    expect(readMapUrl(written).trace).toEqual(path)
    expect(readMapUrl(new URLSearchParams('a=25.771778,-80.26361&b=25.782147,-80.264005')).trace).toEqual(
      path,
    )
    expect(readMapUrl(new URLSearchParams('t=25.7,-80.2')).trace).toBeNull()
    const strict = writeMapUrl('trace', null, path, { snap: false, original: true })
    expect(readMapUrl(strict).options).toEqual({ snap: false, original: true })
    expect(readMapUrl(written).options).toEqual({ snap: true, original: false })
  })
})

describe('celdas de parcelas (PEN-33)', () => {
  it('cubre la vista con celdas fijas y no pide nada si serían demasiadas', () => {
    const cells = cellsFor({ west: -80.2655, south: 25.7705, east: -80.2605, north: 25.7745 })
    expect(cells).toHaveLength(4)
    expect(cells[0]).toEqual({ west: -80.268, south: 25.768, east: -80.264, north: 25.772 })
    expect(cellsFor({ west: -80.4, south: 25.7, east: -80.2, north: 25.9 })).toEqual([])
  })
})
