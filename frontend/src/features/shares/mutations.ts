import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import { normalizeShare } from '../../lib/normalize'
import { invalidateAfterShareWrite } from '../../lib/query/invalidation'
import type { AccessLevel, ApiShare } from '../../lib/types'

export type Recipient = { email: string } | { groupId: string }
export type CreateShareInput = {
  recipients: Recipient[]
  accessLevel: Exclude<AccessLevel, 'OWNER'>
  sendEmail: boolean
  subject?: string
  message?: string
}
type ApiCreateResult = { created?: ApiShare[]; skipped?: { recipient: Recipient; reason: string }[] }

export function useShareMutations(sheetId: string) {
  const queryClient = useQueryClient()
  const path = `/api/sheets/${encodeURIComponent(sheetId)}/shares`
  const invalidate = () => invalidateAfterShareWrite(queryClient, [sheetId])
  const create = useMutation({
    mutationFn: async (input: CreateShareInput) => {
      const body = {
        recipients: input.recipients.map((recipient) =>
          'groupId' in recipient ? { group_id: recipient.groupId } : recipient,
        ),
        access_level: input.accessLevel,
        send_email: input.sendEmail,
        ...(input.sendEmail && input.subject ? { subject: input.subject } : {}),
        ...(input.sendEmail && input.message ? { message: input.message } : {}),
      }
      const result = await api<ApiCreateResult>(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      return { created: (result.created ?? []).map(normalizeShare), skipped: result.skipped ?? [] }
    },
    onSuccess: invalidate,
  })
  const update = useMutation({
    mutationFn: (input: { shareId: string; accessLevel: Exclude<AccessLevel, 'OWNER'> }) =>
      api<ApiShare>(`${path}/${encodeURIComponent(input.shareId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_level: input.accessLevel }),
      }).then(normalizeShare),
    onSuccess: invalidate,
  })
  const remove = useMutation({
    mutationFn: (shareId: string) =>
      api<void>(`${path}/${encodeURIComponent(shareId)}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  })
  return { create, update, remove }
}
