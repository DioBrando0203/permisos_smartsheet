import { describe, expect, it } from 'vitest'
import {
  normalizeSheetActivity,
  normalizeSheetAudit,
  normalizeSheetAutomations,
} from './normalizeSheetInsights'
import { normalizeContact, normalizeGroup } from './normalize'
import {
  activityFixture,
  auditFixture,
  automationsFixture,
  contactsFixture,
  groupsFixture,
} from '../test/fixtures/sheets'

describe('normalizadores de detalles de hoja', () => {
  it('conservan los campos de auditoría, actividad y automatizaciones del contrato', () => {
    expect(normalizeSheetAudit(auditFixture).alerts[0]?.people[0]?.accessLevel).toBe('EDITOR')
    expect(normalizeSheetActivity(activityFixture).changedRows[0]?.modifiedBy.name).toBe('Persona Uno')
    expect(normalizeSheetAutomations(automationsFixture).automations[0]?.recipientColumns[0]?.isContact).toBe(
      false,
    )
  })

  it('normaliza contactos y grupos para el autocompletado', () => {
    expect(normalizeContact(contactsFixture[0] ?? {}).email).toBe('persona1@example.com')
    expect(normalizeGroup(groupsFixture[0] ?? {}).memberCount).toBe(2)
  })
})
