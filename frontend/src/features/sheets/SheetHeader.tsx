import { ArrowClockwise20Regular, Open20Regular } from '@fluentui/react-icons'
import { Button, Skeleton } from '../../components/ui'
import { formatRelativeTime } from '../../lib/formatters'
import type { Sheet } from '../../lib/types'

export function SheetHeader({
  sheet,
  loading,
  onRefresh,
}: {
  sheet?: Sheet
  loading: boolean
  onRefresh: () => void
}) {
  if (loading || !sheet)
    return (
      <div className="sheet-header" aria-busy="true">
        <Skeleton variant="title" />
      </div>
    )
  return (
    <header className="sheet-header">
      <div>
        <h1>{sheet.name}</h1>
        <p>
          {sheet.modifiedAt
            ? `Actualizado ${formatRelativeTime(sheet.modifiedAt)}`
            : 'Fecha de modificación no disponible'}
        </p>
      </div>
      <div className="sheet-header__actions">
        {sheet.permalink && (
          <a className="button button--secondary" href={sheet.permalink} target="_blank" rel="noreferrer">
            <Open20Regular aria-hidden="true" />
            Abrir en Smartsheet
          </a>
        )}
        <Button appearance="secondary" onClick={onRefresh}>
          <ArrowClockwise20Regular aria-hidden="true" />
          Actualizar
        </Button>
      </div>
    </header>
  )
}
