import { describe, expect, it } from 'vitest'
import { normalizeShareList } from '../../../lib/normalize'
import { sharesFixture } from '../../../test/fixtures/sheets'
import { groupShares } from './groupShares'

describe('groupShares', () => {
  it('une el acceso propio y heredado de la misma persona', () => {
    const grouped = groupShares(normalizeShareList(sharesFixture).shares)
    expect(grouped).toHaveLength(1)
    expect(grouped[0]).toMatchObject({ id: 'same', accessLevel: 'EDITOR', scopes: ['ITEM', 'WORKSPACE'] })
  })
})
