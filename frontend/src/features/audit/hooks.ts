import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeSheetAudit } from '../../lib/normalizeSheetInsights'
import { queryKeys } from '../../lib/query/keys'
import type { ApiSheetAudit } from '../../lib/sheetInsights'

export function useSheetAudit(sheetId: string) {
  return useQuery({
    queryKey: queryKeys.audit(sheetId),
    queryFn: () =>
      api<ApiSheetAudit>(`/api/sheets/${encodeURIComponent(sheetId)}/audit`).then(normalizeSheetAudit),
    enabled: Boolean(sheetId),
  })
}
