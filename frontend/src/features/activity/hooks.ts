import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeSheetActivity } from '../../lib/normalizeSheetInsights'
import { queryKeys } from '../../lib/query/keys'
import type { ApiSheetActivity } from '../../lib/sheetInsights'

export function useSheetActivity(sheetId: string, days: number) {
  return useQuery({
    queryKey: queryKeys.activity(sheetId, days),
    queryFn: () =>
      api<ApiSheetActivity>(`/api/sheets/${encodeURIComponent(sheetId)}/activity?days=${days}`).then(
        normalizeSheetActivity,
      ),
    enabled: Boolean(sheetId),
  })
}
