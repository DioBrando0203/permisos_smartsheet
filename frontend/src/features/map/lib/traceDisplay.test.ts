import { describe, expect, it } from 'vitest'
import { mapTraceFixture } from '../../../test/fixtures/map'
import { normalizeMapTrace } from '../normalize'
import { needsTraceReview, officialBounds, officialLines } from './traceDisplay'

describe('resultado ajustado del trazo', () => {
  it('usa sólo geometrías LRS de filas y calcula sus límites completos', () => {
    const trace = normalizeMapTrace(mapTraceFixture)
    expect(officialLines(trace)).toEqual([
      [
        [-80.26361, 25.771778],
        [-80.264005, 25.782147],
      ],
    ])
    expect(officialBounds(trace)).toEqual({
      west: -80.264005,
      south: 25.771778,
      east: -80.26361,
      north: 25.782147,
    })
  })

  it('permite conservar y encuadrar el dibujo si hay partes sin resolver', () => {
    const trace = normalizeMapTrace({ ...mapTraceFixture, warnings: ['TRACE_PARTIAL'] })
    expect(needsTraceReview(trace)).toBe(true)
    expect(officialBounds(trace, [{ lat: 25.8, lon: -80.25 }])?.north).toBe(25.8)
    expect(needsTraceReview(normalizeMapTrace(mapTraceFixture))).toBe(false)
  })

  it('conserva datos desconocidos en el normalizador', () => {
    const trace = normalizeMapTrace({ length_mi: null, rows: [{ length_mi: null }] })
    expect(trace.lengthMi).toBeNull()
    expect(trace.rows[0].lengthMi).toBeNull()
    expect(trace.matchedPercent).toBeNull()
  })
})
