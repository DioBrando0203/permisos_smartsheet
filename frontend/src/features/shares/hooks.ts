import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeContact, normalizeGroup, normalizeShareList } from '../../lib/normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiContact, ApiGroup, ApiShareList } from '../../lib/types'

export function useShares(sheetId: string) {
  return useQuery({
    queryKey: queryKeys.shares(sheetId),
    queryFn: () =>
      api<ApiShareList>(`/api/sheets/${encodeURIComponent(sheetId)}/shares`).then(normalizeShareList),
    enabled: Boolean(sheetId),
  })
}

export function useContacts(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.contacts(),
    queryFn: () => api<ApiContact[]>('/api/contacts').then((contacts) => contacts.map(normalizeContact)),
    enabled,
  })
}

export function useGroups(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.groups(),
    queryFn: () => api<ApiGroup[]>('/api/groups').then((groups) => groups.map(normalizeGroup)),
    enabled,
  })
}
