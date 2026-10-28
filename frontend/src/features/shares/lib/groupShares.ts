import { accessLevels } from '../../../lib/accessLevels'
import type { Share } from '../../../lib/types'

export type GroupedShare = Share & { scopes: Share['scope'][] }

function personKey(share: Share): string {
  return share.type === 'GROUP'
    ? `group:${share.groupId ?? share.id}`
    : `user:${share.userId ?? share.email ?? share.id}`
}

export function groupShares(shares: Share[]): GroupedShare[] {
  const grouped = new Map<string, GroupedShare>()
  for (const share of shares) {
    const key = personKey(share)
    const existing = grouped.get(key)
    if (!existing) {
      grouped.set(key, { ...share, scopes: [share.scope] })
      continue
    }
    const effective =
      accessLevels[share.accessLevel].rank > accessLevels[existing.accessLevel].rank ? share : existing
    grouped.set(key, { ...effective, scopes: [...existing.scopes, share.scope] })
  }
  return [...grouped.values()].sort((a, b) => {
    const level = accessLevels[b.accessLevel].rank - accessLevels[a.accessLevel].rank
    if (level) return level
    return displayName(a).localeCompare(displayName(b), 'es')
  })
}

export function displayName(share: Pick<Share, 'name' | 'email'>): string {
  return share.name || share.email || 'Sin nombre'
}
