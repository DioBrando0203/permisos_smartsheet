import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeHealth, normalizeMe } from '../../lib/normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiHealth, ApiMe } from '../../lib/types'

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: () => api<ApiHealth>('/api/health').then(normalizeHealth),
    retry: false,
    refetchInterval: 60_000,
  })
}

export function useMe() {
  return useQuery({
    queryKey: queryKeys.me(),
    queryFn: () => api<ApiMe>('/api/me').then(normalizeMe),
  })
}
