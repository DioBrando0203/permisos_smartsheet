import type { ApiRevokePlan } from '../../features/people/revoke'

export const revokePlanFixture = {
  person: {
    key: 'persona1@example.com',
    type: 'USER',
    name: 'Persona Uno',
    email: 'persona1@example.com',
  },
  dry_run: true,
  counts: { REMOVE: 1, SKIP: 1 },
  steps: [
    { action: 'REMOVE', status: 'planned', sheet_id: '100', sheet_name: 'Plan 2026', reason: null },
    {
      action: 'SKIP',
      status: 'not_applicable',
      sheet_id: '200',
      sheet_name: 'Hoja heredada',
      reason: 'INHERITED',
    },
  ],
} satisfies ApiRevokePlan
