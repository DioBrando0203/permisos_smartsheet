import type { ApiContact, ApiGroup, ApiShareList, ApiSheetList } from '../../lib/types'
import type { ApiSheetActivity, ApiSheetAudit, ApiSheetAutomations } from '../../lib/sheetInsights'

export const sheetsFixture = {
  sheets: [
    {
      id: '100',
      name: 'Plan 2026',
      access_level: 'ADMIN',
      can_manage_shares: true,
      permalink: 'https://app.smartsheet.com/sheets/example',
      modified_at: '2026-10-27T12:00:00Z',
      has_dynamic_view: true,
      owner_email: 'admin@example.com',
      in_my_list: true,
    },
    {
      id: '200',
      name: 'Ñandú',
      access_level: null,
      can_manage_shares: false,
      permalink: null,
      modified_at: null,
      has_dynamic_view: false,
      owner_email: 'owner@example.com',
      in_my_list: false,
    },
  ],
  total: 2,
  total_mine: 1,
  loaded_at: '2026-10-27T12:00:00Z',
} satisfies ApiSheetList

export const sharesFixture = {
  sheet_id: '100',
  shares: [
    {
      id: 'same',
      type: 'USER',
      user_id: 'person-1',
      group_id: null,
      email: 'persona1@example.com',
      name: 'Persona Uno',
      access_level: 'EDITOR',
      scope: 'ITEM',
      editable: true,
      locked_reason: null,
    },
    {
      id: 'same',
      type: 'USER',
      user_id: 'person-1',
      group_id: null,
      email: 'persona1@example.com',
      name: 'Persona Uno',
      access_level: 'VIEWER',
      scope: 'WORKSPACE',
      editable: false,
      locked_reason: 'INHERITED',
    },
  ],
  loaded_at: '2026-10-27T12:00:00Z',
} satisfies ApiShareList

export const contactsFixture = [
  { id: 'contact-1', email: 'persona1@example.com', name: 'Persona Uno' },
] satisfies ApiContact[]

export const groupsFixture = [
  { id: 'group-1', name: 'Equipo de prueba', description: 'Grupo sintético', member_count: 2 },
] satisfies ApiGroup[]

export const auditFixture = {
  sheet: sheetsFixture.sheets[0],
  total: 3,
  by_level: { EDITOR: 2, VIEWER: 1 },
  by_scope: { ITEM: 2, WORKSPACE: 1 },
  by_domain: [
    { domain: 'example.com', count: 2, is_personal: false },
    { domain: 'correo.test', count: 1, is_personal: true },
  ],
  org_known: true,
  external_count: 1,
  unnamed_count: 0,
  not_in_contacts_count: 1,
  alerts: [
    {
      code: 'EXTERNAL_CAN_SHARE',
      severity: 'high',
      message: 'Una persona externa puede compartir',
      count: 1,
      people: [
        {
          key: 'persona1@example.com',
          type: 'USER',
          name: 'Persona Uno',
          email: 'persona1@example.com',
          access_level: 'EDITOR',
        },
      ],
    },
  ],
} satisfies ApiSheetAudit

export const activityFixture = {
  sheet: sheetsFixture.sheets[0],
  days: 30,
  rows_total: 24,
  changed_rows_total: 1,
  changed_rows: [
    {
      row_id: 'row-1',
      row_number: 1,
      label: 'Tarea uno',
      modified_at: '2026-10-27T12:00:00Z',
      modified_by: { name: 'Persona Uno', email: 'persona1@example.com' },
    },
  ],
  editors: [
    {
      name: 'Persona Uno',
      email: 'persona1@example.com',
      rows_changed: 1,
      last_change: '2026-10-27T12:00:00Z',
      access_level: 'EDITOR',
    },
  ],
  idle_editors: [
    {
      key: 'persona2@example.com',
      name: 'Persona Dos',
      email: 'persona2@example.com',
      access_level: 'EDITOR',
    },
  ],
  limitations: ['Una cuenta concentra más del 80 % de las filas modificadas.'],
} satisfies ApiSheetActivity

export const automationsFixture = {
  sheet: sheetsFixture.sheets[0],
  counts: { ok: 1, with_problems: 0, disabled: 1 },
  automations: [
    {
      id: 'auto-1',
      name: 'Avisar cambios',
      enabled: true,
      status: 'ok',
      action_type: 'Alerta',
      frequency: 'Al cambiar',
      recipient_emails: ['persona1@example.com'],
      recipient_columns: [
        { id: 'col-1', title: 'Diseñador', type: 'TEXT_NUMBER', is_contact: false, exists: true },
      ],
      notify_all_shared: false,
      smartsheet_reason: null,
      problems: [],
    },
  ],
} satisfies ApiSheetAutomations
