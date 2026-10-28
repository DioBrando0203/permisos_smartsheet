import type {
  ApiHealth,
  ApiContact,
  ApiGroup,
  ApiMe,
  ApiPeopleResponse,
  ApiPerson,
  ApiPersonDetail,
  ApiShare,
  ApiShareList,
  ApiSheet,
  ApiSheetList,
  Health,
  Contact,
  Group,
  Me,
  PeopleResponse,
  Person,
  PersonDetail,
  PersonSheetAccess,
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

export function normalizePerson(source: ApiPerson): Person {
  return {
    key: source.key ?? '',
    type: source.type ?? 'USER',
    name: source.name ?? null,
    email: source.email ?? null,
    sheetCount: source.sheet_count ?? 0,
    highestLevel: source.highest_level ?? null,
    isContact: source.is_contact ?? false,
    isOrgMember: source.is_org_member ?? false,
    isTokenOwner: source.is_token_owner ?? false,
    lastLogin: source.last_login ?? null,
  }
}

export function normalizePeople(source: ApiPeopleResponse): PeopleResponse {
  return {
    people: (source.people ?? []).map(normalizePerson),
    total: source.total ?? 0,
    incomplete: source.incomplete ?? false,
    failedSheets: (source.failed_sheets ?? []).map((sheet) => ({
      sheetId: sheet.sheet_id ?? '',
      sheetName: sheet.sheet_name ?? 'Hoja sin nombre',
      code: sheet.code ?? 'UNKNOWN',
    })),
    loadedAt: source.loaded_at ?? null,
  }
}

export function normalizePersonDetail(source: ApiPersonDetail): PersonDetail {
  return {
    person: normalizePerson(source.person ?? {}),
    sheets: (source.sheets ?? []).map((sheet): PersonSheetAccess => ({
      sheetId: sheet.sheet_id ?? '',
      sheetName: sheet.sheet_name ?? 'Hoja sin nombre',
      shareId: sheet.share_id ?? '',
      accessLevel: sheet.access_level ?? 'VIEWER',
      scope: sheet.scope ?? 'ITEM',
      editable: sheet.editable ?? false,
      lockedReason: sheet.locked_reason ?? null,
    })),
  }
}

export function normalizeContact(source: ApiContact): Contact {
  return { id: source.id ?? '', email: source.email ?? '', name: source.name ?? null }
}

export function normalizeGroup(source: ApiGroup): Group {
  return {
    id: source.id ?? '',
    name: source.name ?? 'Grupo sin nombre',
    description: source.description ?? null,
    memberCount: source.member_count ?? null,
  }
}
