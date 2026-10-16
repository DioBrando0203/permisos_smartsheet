import type { Severity } from './types'

export const severity: Record<Severity, { label: string; tone: 'danger' | 'warning' | 'info' }> = {
  high: { label: 'Alta', tone: 'danger' },
  medium: { label: 'Media', tone: 'warning' },
  info: { label: 'Informativa', tone: 'info' },
}
