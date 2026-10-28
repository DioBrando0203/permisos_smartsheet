import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeSheetAutomations } from '../../lib/normalizeSheetInsights'
import { queryKeys } from '../../lib/query/keys'
import type { ApiSheetAutomations } from '../../lib/sheetInsights'

export function useSheetAutomations(sheetId: string) {
  return useQuery({
    queryKey: queryKeys.automations(sheetId),
    queryFn: () =>
      api<ApiSheetAutomations>(`/api/sheets/${encodeURIComponent(sheetId)}/automations`).then(
        normalizeSheetAutomations,
      ),
    enabled: Boolean(sheetId),
  })
}
