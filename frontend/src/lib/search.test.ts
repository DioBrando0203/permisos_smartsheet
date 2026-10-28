import { describe, expect, it } from 'vitest'
import { includesSearch } from './search'

describe('includesSearch', () => {
  it('ignora mayúsculas y tildes', () => {
    expect(includesSearch('Ñandú', 'nandu')).toBe(true)
    expect(includesSearch('Plan 2026', 'PLAN de 2026')).toBe(true)
  })
})
