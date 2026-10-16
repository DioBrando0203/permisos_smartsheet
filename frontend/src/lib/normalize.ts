import type { ApiHealth, ApiMe, Health, Me } from './types'

export function normalizeHealth(source: ApiHealth): Health {
  return {
    status: 'ok',
    smartsheet: source.smartsheet === 'missing_token' ? 'missing_token' : 'configured',
    readOnly: source.read_only ?? true,
  }
}

export function normalizeMe(source: ApiMe): Me {
  return {
    userId: source.user_id ?? '',
    email: source.email ?? '',
    name: source.name ?? null,
    accountName: source.account_name ?? null,
    isSystemAdmin: source.is_system_admin ?? false,
  }
}
