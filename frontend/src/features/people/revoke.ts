import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { invalidateAfterShareWrite } from '../../lib/query/invalidation'
import type { Person } from '../../lib/types'

export type RevokeStep = {
  action: string
  status: string
  sheetId: string
  sheetName: string
  reason: string | null
}
export type RevokePlan = {
  person: Person
  dryRun: boolean
  counts: Record<string, number>
  steps: RevokeStep[]
}
export type ApiRevokePlan = {
  person?: { key?: string; type?: 'USER' | 'GROUP'; name?: string | null; email?: string | null }
  dry_run?: boolean
  counts?: Record<string, number>
  steps?: {
    action?: string
    status?: string
    sheet_id?: string
    sheet_name?: string
    reason?: string | null
  }[]
}

export function normalizeRevokePlan(source: ApiRevokePlan): RevokePlan {
  return {
    person: {
      key: source.person?.key ?? '',
      type: source.person?.type ?? 'USER',
      name: source.person?.name ?? null,
      email: source.person?.email ?? null,
      sheetCount: 0,
      highestLevel: null,
      isContact: false,
      isOrgMember: false,
      isTokenOwner: false,
      lastLogin: null,
    },
    dryRun: source.dry_run ?? true,
    counts: source.counts ?? {},
    steps: (source.steps ?? []).map((step) => ({
      action: step.action ?? 'SKIP',
      status: step.status ?? 'planned',
      sheetId: step.sheet_id ?? '',
      sheetName: step.sheet_name ?? 'Hoja sin nombre',
      reason: step.reason ?? null,
    })),
  }
}

export function useRevokePerson(key: string) {
  const queryClient = useQueryClient()
  const path = `/api/users/${encodeURIComponent(key)}/revoke`
  const send = (sheetIds: string[] | null, dryRun: boolean) =>
    api<ApiRevokePlan>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sheet_ids: sheetIds, dry_run: dryRun }),
    }).then(normalizeRevokePlan)
  const simulate = useMutation({ mutationFn: (sheetIds: string[] | null) => send(sheetIds, true) })
  const execute = useMutation({
    mutationFn: (sheetIds: string[] | null) => send(sheetIds, false),
    onSuccess: (plan) =>
      invalidateAfterShareWrite(
        queryClient,
        plan.steps.map((step) => step.sheetId),
      ),
  })
  return { simulate, execute }
}
