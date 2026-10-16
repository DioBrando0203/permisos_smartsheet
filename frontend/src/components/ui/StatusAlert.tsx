import type { ReactNode } from 'react'
import {
  CheckmarkCircle20Filled,
  ErrorCircle20Filled,
  Info20Filled,
  Warning20Filled,
} from '@fluentui/react-icons'

type Props = { tone: 'error' | 'warning' | 'success' | 'info'; children: ReactNode; title?: string }
const icons = {
  error: ErrorCircle20Filled,
  warning: Warning20Filled,
  success: CheckmarkCircle20Filled,
  info: Info20Filled,
}

export function StatusAlert({ tone, title, children }: Props) {
  const Icon = icons[tone]
  return (
    <div className={`status-alert status-alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon className="status-alert__icon" aria-hidden="true" />
      <div>
        {title && <strong>{title} </strong>}
        {children}
      </div>
    </div>
  )
}
