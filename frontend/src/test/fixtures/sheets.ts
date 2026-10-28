import type { ApiShareList, ApiSheetList } from '../../lib/types'

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
