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
