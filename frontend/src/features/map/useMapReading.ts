import { useMutation, useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query'
import { api } from '../../lib/api'

const staleTime = 10 * 60 * 1000
type RefreshRequest = { path: string; key: QueryKey }

/** Actualizar evita ambas cachés; una respuesta tardía se guarda en la selección que la pidió. */
export function useMapReading<Raw, Result>(
  key: QueryKey,
  path: string | null,
  normalize: (raw: Raw) => Result,
) {
  const client = useQueryClient()
  const query = useQuery({
    queryKey: key,
    queryFn: () => {
      if (!path) throw new Error('Selecciona un lugar o dibuja un trazo.')
      return api<Raw>(path).then(normalize)
    },
    enabled: path !== null,
    staleTime,
  })
  const refresh = useMutation({
    mutationFn: async (request: RefreshRequest) => {
      await client.cancelQueries({ queryKey: request.key, exact: true })
      return api<Raw>(`${request.path}&refresh=true`).then(normalize)
    },
    onSuccess: (data, request) => client.setQueryData(request.key, data),
  })
  const current = refresh.variables?.path === path
  return {
    ...query,
    error: (current && refresh.error) || query.error,
    isFetching: query.isFetching || (current && refresh.isPending),
    refresh: () => {
      if (path && !refresh.isPending) refresh.mutate({ path, key })
    },
  }
}
