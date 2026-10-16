import type { ReactNode } from 'react'

type Props = { children: ReactNode; tone?: 'neutral' | 'warning' | 'danger' | 'info' }

export function Badge({ children, tone = 'neutral' }: Props) {
  return <span className={`badge badge--${tone}`}>{children}</span>
}
