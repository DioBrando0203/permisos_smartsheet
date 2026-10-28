import { normalizeSheet } from './normalize'
import type {
  ApiSheetActivity,
  ApiSheetAudit,
  ApiSheetAutomations,
  Automation,
  SheetActivity,
  SheetAudit,
  SheetAutomations,
} from './sheetInsights'

const actor = (source: { email?: string | null; name?: string | null } = {}) => ({
  email: source.email ?? null,
  name: source.name ?? null,
})

export function normalizeSheetAudit(source: ApiSheetAudit): SheetAudit {
  return {
    sheet: normalizeSheet(source.sheet ?? {}),
    total: source.total ?? 0,
    byLevel: source.by_level ?? {},
    byScope: source.by_scope ?? {},
    byDomain: (source.by_domain ?? []).map((item) => ({
      domain: item.domain ?? 'Sin dominio',
      count: item.count ?? 0,
      isPersonal: item.is_personal ?? false,
    })),
    orgKnown: source.org_known ?? false,
    externalCount: source.external_count ?? null,
    unnamedCount: source.unnamed_count ?? 0,
    notInContactsCount: source.not_in_contacts_count ?? 0,
    alerts: (source.alerts ?? []).map((alert) => ({
      code: alert.code ?? 'UNKNOWN',
      severity: alert.severity ?? 'info',
      message: alert.message ?? 'Sin detalle',
      count: alert.count ?? 0,
      people: (alert.people ?? []).map((person) => ({
        key: person.key ?? '',
        type: person.type ?? 'USER',
        name: person.name ?? null,
        email: person.email ?? null,
        accessLevel: person.access_level ?? 'VIEWER',
      })),
    })),
  }
}

export function normalizeSheetActivity(source: ApiSheetActivity): SheetActivity {
  return {
    sheet: normalizeSheet(source.sheet ?? {}),
    days: source.days ?? 30,
    rowsTotal: source.rows_total ?? 0,
    changedRowsTotal: source.changed_rows_total ?? 0,
    changedRows: (source.changed_rows ?? []).map((row) => ({
      rowId: row.row_id ?? '',
      rowNumber: row.row_number ?? 0,
      label: row.label ?? null,
      modifiedAt: row.modified_at ?? null,
      modifiedBy: actor(row.modified_by),
    })),
    editors: (source.editors ?? []).map((editor) => ({
      ...actor(editor),
      rowsChanged: editor.rows_changed ?? 0,
      lastChange: editor.last_change ?? null,
      accessLevel: editor.access_level ?? null,
    })),
    idleEditors: (source.idle_editors ?? []).map((editor) => ({
      key: editor.key ?? '',
      ...actor(editor),
      accessLevel: editor.access_level ?? 'VIEWER',
    })),
    limitations: source.limitations ?? [],
  }
}

function normalizeAutomation(source: {
  id?: string
  name?: string
  enabled?: boolean
  status?: Automation['status']
  action_type?: string | null
  frequency?: string | null
  recipient_emails?: string[]
  recipient_columns?: { id?: string; title?: string; type?: string; is_contact?: boolean; exists?: boolean }[]
  notify_all_shared?: boolean
  smartsheet_reason?: string | null
  problems?: { code?: string; message?: string }[]
}): Automation {
  return {
    id: source.id ?? '',
    name: source.name ?? 'Automatización sin nombre',
    enabled: source.enabled ?? false,
    status: source.status ?? 'disabled',
    actionType: source.action_type ?? null,
    frequency: source.frequency ?? null,
    recipientEmails: source.recipient_emails ?? [],
    recipientColumns: (source.recipient_columns ?? []).map((column) => ({
      id: column.id ?? '',
      title: column.title ?? 'Columna sin nombre',
      type: column.type ?? 'Desconocido',
      isContact: column.is_contact ?? false,
      exists: column.exists ?? false,
    })),
    notifyAllShared: source.notify_all_shared ?? false,
    smartsheetReason: source.smartsheet_reason ?? null,
    problems: (source.problems ?? []).map((problem) => ({
      code: problem.code ?? 'UNKNOWN',
      message: problem.message ?? 'Sin detalle',
    })),
  }
}

export function normalizeSheetAutomations(source: ApiSheetAutomations): SheetAutomations {
  return {
    sheet: normalizeSheet(source.sheet ?? {}),
    counts: source.counts ?? {},
    automations: (source.automations ?? []).map(normalizeAutomation),
  }
}
