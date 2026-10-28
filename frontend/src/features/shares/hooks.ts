import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeShareList } from '../../lib/normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiShareList } from '../../lib/types'

export function useShares(sheetId: string) {
  return useQuery({
    queryKey: queryKeys.shares(sheetId),
    queryFn: () =>
      api<ApiShareList>(`/api/sheets/${encodeURIComponent(sheetId)}/shares`).then(normalizeShareList),
    enabled: Boolean(sheetId),
  })
}
