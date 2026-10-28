import { describe, expect, it } from 'vitest'
import { revokePlanFixture } from '../../test/fixtures/people'
import { normalizeRevokePlan } from './revoke'

describe('normalizeRevokePlan', () => {
  it('mantiene los pasos y motivos de la simulación de revocación', () => {
    const plan = normalizeRevokePlan(revokePlanFixture)
    expect(plan.counts).toEqual({ REMOVE: 1, SKIP: 1 })
    expect(plan.steps[1]).toMatchObject({ sheetName: 'Hoja heredada', reason: 'INHERITED' })
  })
})
