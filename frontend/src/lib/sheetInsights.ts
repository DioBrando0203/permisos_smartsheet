import type { AccessLevel, ApiSheet, Severity, Sheet } from './types'

export type AuditPerson = {
  key: string
  type: 'USER' | 'GROUP'
  name: string | null
  email: string | null
  accessLevel: AccessLevel
}
export type AuditAlert = {
  code: string
  severity: Severity
  message: string
  count: number
  people: AuditPerson[]
}
export type SheetAudit = {
  sheet: Sheet
  total: number
  byLevel: Record<string, number>
  byScope: Record<string, number>
  byDomain: { domain: string; count: number; isPersonal: boolean }[]
  orgKnown: boolean
  externalCount: number | null
  unnamedCount: number
  notInContactsCount: number
  alerts: AuditAlert[]
}

export type ApiSheetAudit = {
  sheet?: ApiSheet
  total?: number
  by_level?: Record<string, number>
  by_scope?: Record<string, number>
  by_domain?: { domain?: string; count?: number; is_personal?: boolean }[]
  org_known?: boolean
  external_count?: number | null
  unnamed_count?: number
  not_in_contacts_count?: number
  alerts?: {
    code?: string
    severity?: Severity
    message?: string
    count?: number
    people?: ApiAuditPerson[]
  }[]
}
type ApiAuditPerson = {
  key?: string
  type?: 'USER' | 'GROUP'
  name?: string | null
  email?: string | null
  access_level?: AccessLevel
}

export type SheetActivity = {
  sheet: Sheet
  days: number
  rowsTotal: number
  changedRowsTotal: number
  changedRows: ChangedRow[]
  editors: ActivityEditor[]
  idleEditors: IdleEditor[]
  limitations: string[]
}
export type ChangedRow = {
  rowId: string
  rowNumber: number
  label: string | null
  modifiedAt: string | null
  modifiedBy: ActivityActor
}
export type ActivityActor = { email: string | null; name: string | null }
export type ActivityEditor = ActivityActor & {
  rowsChanged: number
  lastChange: string | null
  accessLevel: AccessLevel | null
}
export type IdleEditor = { key: string; email: string | null; name: string | null; accessLevel: AccessLevel }
export type ApiSheetActivity = {
  sheet?: ApiSheet
  days?: number
  rows_total?: number
  changed_rows_total?: number
  changed_rows?: ApiChangedRow[]
  editors?: ApiActivityEditor[]
  idle_editors?: ApiIdleEditor[]
  limitations?: string[]
}
type ApiChangedRow = {
  row_id?: string
  row_number?: number
  label?: string | null
  modified_at?: string | null
  modified_by?: ApiActivityActor
}
type ApiActivityActor = { email?: string | null; name?: string | null }
type ApiActivityEditor = ApiActivityActor & {
  rows_changed?: number
  last_change?: string | null
  access_level?: AccessLevel | null
}
type ApiIdleEditor = { key?: string; email?: string | null; name?: string | null; access_level?: AccessLevel }

export type Automation = {
  id: string
  name: string
  enabled: boolean
  status: 'ok' | 'with_problems' | 'disabled'
  actionType: string | null
  frequency: string | null
  recipientEmails: string[]
  recipientColumns: { id: string; title: string; type: string; isContact: boolean; exists: boolean }[]
  notifyAllShared: boolean
  smartsheetReason: string | null
  problems: { code: string; message: string }[]
}
export type SheetAutomations = { sheet: Sheet; counts: Record<string, number>; automations: Automation[] }
export type ApiSheetAutomations = {
  sheet?: ApiSheet
  counts?: Record<string, number>
  automations?: ApiAutomation[]
}
type ApiAutomation = {
  id?: string
  name?: string
  enabled?: boolean
  status?: 'ok' | 'with_problems' | 'disabled'
  action_type?: string | null
  frequency?: string | null
  recipient_emails?: string[]
  recipient_columns?: { id?: string; title?: string; type?: string; is_contact?: boolean; exists?: boolean }[]
  notify_all_shared?: boolean
  smartsheet_reason?: string | null
  problems?: { code?: string; message?: string }[]
}
