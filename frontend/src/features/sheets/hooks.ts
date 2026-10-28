import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeSheet, normalizeSheetList } from '../../lib/normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiSheet, ApiSheetList } from '../../lib/types'

export function useSheets() {
  return useQuery({
    queryKey: queryKeys.sheets(),
    queryFn: () => api<ApiSheetList>('/api/sheets?scope=all').then(normalizeSheetList),
  })
}

export function useSheet(id: string) {
  return useQuery({
    queryKey: queryKeys.sheet(id),
    queryFn: () => api<ApiSheet>(`/api/sheets/${encodeURIComponent(id)}`).then(normalizeSheet),
    enabled: Boolean(id),
  })
}
