export type Health = {
  status: 'ok'
  smartsheet: 'configured' | 'missing_token'
  readOnly: boolean
}

export type ApiHealth = { status?: string; smartsheet?: string; read_only?: boolean }

export type Me = {
  userId: string
  email: string
  name: string | null
  accountName: string | null
  isSystemAdmin: boolean
}

export type ApiMe = {
  user_id?: string
  email?: string
  name?: string | null
  account_name?: string | null
  is_system_admin?: boolean
}

export type AccessLevel = 'VIEWER' | 'COMMENTER' | 'EDITOR' | 'EDITOR_SHARE' | 'ADMIN' | 'OWNER'
export type Severity = 'high' | 'medium' | 'info'

export type Sheet = {
  id: string
  name: string
  accessLevel: AccessLevel | null
  canManageShares: boolean
  permalink: string | null
  modifiedAt: string | null
  hasDynamicView: boolean
  ownerEmail: string | null
  inMyList: boolean
}

export type SheetList = { sheets: Sheet[]; total: number; totalMine: number; loadedAt: string | null }

export type ShareScope = 'ITEM' | 'WORKSPACE'
export type LockedReason = 'OWNER' | 'INHERITED' | 'NO_PERMISSION' | null

export type Share = {
  id: string
  type: 'USER' | 'GROUP'
  userId: string | null
  groupId: string | null
  email: string | null
  name: string | null
  accessLevel: AccessLevel
  scope: ShareScope
  editable: boolean
  lockedReason: LockedReason
}

export type ShareList = { sheetId: string; shares: Share[]; loadedAt: string | null }

export type ApiSheet = {
  id?: string
  name?: string
  access_level?: AccessLevel | null
  can_manage_shares?: boolean
  permalink?: string | null
  modified_at?: string | null
  has_dynamic_view?: boolean
  owner_email?: string | null
  in_my_list?: boolean
}

export type ApiSheetList = {
  sheets?: ApiSheet[]
  total?: number
  total_mine?: number
  loaded_at?: string | null
}

export type ApiShare = {
  id?: string
  type?: 'USER' | 'GROUP'
  user_id?: string | null
  group_id?: string | null
  email?: string | null
  name?: string | null
  access_level?: AccessLevel
  scope?: ShareScope
  editable?: boolean
  locked_reason?: LockedReason
}

export type ApiShareList = { sheet_id?: string; shares?: ApiShare[]; loaded_at?: string | null }

export type Person = {
  key: string
  type: 'USER' | 'GROUP'
  name: string | null
  email: string | null
  sheetCount: number
  highestLevel: AccessLevel | null
  isContact: boolean
  isOrgMember: boolean
  isTokenOwner: boolean
  lastLogin: string | null
}

export type PersonSheetAccess = {
  sheetId: string
  sheetName: string
  shareId: string
  accessLevel: AccessLevel
  scope: ShareScope
  editable: boolean
  lockedReason: LockedReason
}

export type PeopleResponse = {
  people: Person[]
  total: number
  incomplete: boolean
  failedSheets: { sheetId: string; sheetName: string; code: string }[]
  loadedAt: string | null
}

export type PersonDetail = { person: Person; sheets: PersonSheetAccess[] }

export type ApiPerson = {
  key?: string
  type?: 'USER' | 'GROUP'
  name?: string | null
  email?: string | null
  sheet_count?: number
  highest_level?: AccessLevel | null
  is_contact?: boolean
  is_org_member?: boolean
  is_token_owner?: boolean
  last_login?: string | null
}

export type ApiPeopleResponse = {
  people?: ApiPerson[]
  total?: number
  incomplete?: boolean
  failed_sheets?: { sheet_id?: string; sheet_name?: string; code?: string }[]
  loaded_at?: string | null
}

export type ApiPersonDetail = {
  person?: ApiPerson
  sheets?: {
    sheet_id?: string
    sheet_name?: string
    share_id?: string
    access_level?: AccessLevel
    scope?: ShareScope
    editable?: boolean
    locked_reason?: LockedReason
  }[]
}

export type Contact = { id: string; email: string; name: string | null }
export type Group = { id: string; name: string; description: string | null; memberCount: number | null }

export type ApiContact = { id?: string; email?: string; name?: string | null }
export type ApiGroup = {
  id?: string
  name?: string
  description?: string | null
  member_count?: number | null
}
