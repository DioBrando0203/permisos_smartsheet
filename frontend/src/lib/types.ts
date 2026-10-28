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
