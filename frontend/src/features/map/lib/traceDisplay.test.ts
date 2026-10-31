import { describe, expect, it } from 'vitest'
import { mapTraceFixture } from '../../../test/fixtures/map'
import { normalizeMapTrace } from '../normalize'
import { officialBounds, officialLines } from './traceDisplay'

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
})
