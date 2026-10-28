import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizePeople, normalizePersonDetail } from '../../lib/normalize'
import { queryKeys } from '../../lib/query/keys'
import type { ApiPeopleResponse, ApiPersonDetail } from '../../lib/types'

export function usePeople() {
  return useQuery({
    queryKey: queryKeys.people(),
    queryFn: () => api<ApiPeopleResponse>('/api/users').then(normalizePeople),
  })
}

export function usePerson(key: string) {
  return useQuery({
    queryKey: queryKeys.person(key),
    queryFn: () => api<ApiPersonDetail>(`/api/users/${encodeURIComponent(key)}`).then(normalizePersonDetail),
    enabled: Boolean(key),
  })
}
