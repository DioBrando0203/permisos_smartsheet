import type {
  ApiHealth,
  ApiMe,
  ApiShare,
  ApiShareList,
  ApiSheet,
  ApiSheetList,
  Health,
  Me,
  Share,
  ShareList,
  Sheet,
  SheetList,
} from './types'

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

export function normalizeSheet(source: ApiSheet): Sheet {
  return {
    id: source.id ?? '',
    name: source.name ?? 'Hoja sin nombre',
    accessLevel: source.access_level ?? null,
    canManageShares: source.can_manage_shares ?? false,
    permalink: source.permalink ?? null,
    modifiedAt: source.modified_at ?? null,
    hasDynamicView: source.has_dynamic_view ?? false,
    ownerEmail: source.owner_email ?? null,
    inMyList: source.in_my_list ?? true,
  }
}

export function normalizeSheetList(source: ApiSheetList): SheetList {
  return {
    sheets: (source.sheets ?? []).map(normalizeSheet),
    total: source.total ?? 0,
    totalMine: source.total_mine ?? 0,
    loadedAt: source.loaded_at ?? null,
  }
}

export function normalizeShare(source: ApiShare): Share {
  return {
    id: source.id ?? '',
    type: source.type ?? 'USER',
    userId: source.user_id ?? null,
    groupId: source.group_id ?? null,
    email: source.email ?? null,
    name: source.name ?? null,
    accessLevel: source.access_level ?? 'VIEWER',
    scope: source.scope ?? 'ITEM',
    editable: source.editable ?? false,
    lockedReason: source.locked_reason ?? null,
  }
}

export function normalizeShareList(source: ApiShareList): ShareList {
  return {
    sheetId: source.sheet_id ?? '',
    shares: (source.shares ?? []).map(normalizeShare),
    loadedAt: source.loaded_at ?? null,
  }
}
