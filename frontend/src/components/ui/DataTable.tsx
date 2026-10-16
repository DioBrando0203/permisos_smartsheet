import type { ReactNode } from 'react'

type Props = { caption: string; children: ReactNode }

export function DataTable({ caption, children }: Props) {
  return (
    <div className="data-table">
      <table>
        <caption className="sr-only">{caption}</caption>
        {children}
      </table>
    </div>
  )
}
