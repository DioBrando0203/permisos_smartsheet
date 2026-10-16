import type { QueryClient } from '@tanstack/react-query'
import { queryKeys } from './keys'

export function invalidateAfterShareWrite(queryClient: QueryClient, sheetIds: string[]): Promise<void[]> {
  const invalidations = [
    ...sheetIds.flatMap((sheetId) => [
      queryClient.invalidateQueries({ queryKey: queryKeys.shares(sheetId) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.sheet(sheetId) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.audit(sheetId) }),
    ]),
    queryClient.invalidateQueries({ queryKey: queryKeys.people() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.personRoot() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.reviewRoot() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.accessSummaryRoot() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.compareRoot() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.designersRoot() }),
  ]
  return Promise.all(invalidations)
}
