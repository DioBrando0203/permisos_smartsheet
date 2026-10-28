import { describe, expect, it } from 'vitest'
import { parseRecipientEmails } from './recipients'

describe('parseRecipientEmails', () => {
  it('separa correos y señala duplicados sin repetirlos', () => {
    expect(parseRecipientEmails('a@example.com; b@example.com, A@example.com')).toEqual({
      emails: ['a@example.com', 'b@example.com'],
      duplicates: ['a@example.com'],
      invalid: [],
    })
  })
})
