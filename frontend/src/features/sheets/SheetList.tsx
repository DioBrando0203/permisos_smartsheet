import { ArrowClockwise20Regular, ArrowDownload20Regular, Document24Regular } from '@fluentui/react-icons'
import { Link } from 'react-router'
import { Badge, Button, EmptyState, SearchBox, Skeleton, StatusAlert } from '../../components/ui'
import { errorMessage } from '../../lib/errorMessages'
import { formatRelativeTime } from '../../lib/formatters'
import { sheetPath } from '../../lib/routes'
import { includesSearch } from '../../lib/search'
import type { Sheet, SheetList as SheetListType } from '../../lib/types'

export type SheetScope = 'all' | 'mine' | 'others'
type Props = {
  result?: SheetListType
  loading: boolean
  error: Error | null
  scope: SheetScope
  query: string
  selectedId?: string
  onScope: (scope: SheetScope) => void
  onQuery: (value: string) => void
  onRefresh: () => void
}

function filteredSheets(sheets: Sheet[], scope: SheetScope, query: string): Sheet[] {
  return sheets.filter(
    (sheet) =>
      (scope === 'mine' ? sheet.inMyList : scope === 'others' ? !sheet.inMyList : true) &&
      includesSearch(`${sheet.name} ${sheet.ownerEmail ?? ''}`, query),
  )
}

function exportPath(scope: SheetScope, query: string): string {
  const params = new URLSearchParams({ scope: scope === 'others' ? 'org_only' : scope, q: query })
  return `/api/export/access.csv?${params.toString()}`
}

export function SheetList({
  result,
  loading,
  error,
  scope,
  query,
  selectedId,
  onScope,
  onQuery,
  onRefresh,
}: Props) {
  if (loading) return <SheetListSkeleton />
  if (error || !result)
    return (
      <StatusAlert tone="error" title="No se pudieron cargar las hojas">
        {errorMessage('BACKEND_UNREACHABLE', error?.message).text}{' '}
        <Button appearance="subtle" onClick={onRefresh}>
          Reintentar
        </Button>
      </StatusAlert>
    )
  const sheets = filteredSheets(result.sheets, scope, query)
  return (
    <section className="sheet-list">
      <header className="sheet-list__header">
        <div>
          <h1>Hojas</h1>
          <span role="status">
            {sheets.length} de {result.total} hojas
          </span>
        </div>
        <div className="sheet-list__actions">
          <Button
            appearance="subtle"
            iconOnly
            aria-label="Actualizar hojas"
            title="Actualizar"
            onClick={onRefresh}
          >
            <ArrowClockwise20Regular aria-hidden="true" />
          </Button>
          <a
            className="button button--secondary button--sm"
            href={exportPath(scope, query)}
            download
            title="Incluye correos reales: compártalo sólo con quien lo necesite"
          >
            <ArrowDownload20Regular aria-hidden="true" />
            Exportar a Excel
          </a>
        </div>
      </header>
      <div className="sheet-list__filters">
        <label>
          Alcance
          <select value={scope} onChange={(event) => onScope(event.target.value as SheetScope)}>
            <option value="all">Todas</option>
            <option value="mine">Mías</option>
            <option value="others">De otras personas</option>
          </select>
        </label>
        <SearchBox
          value={query}
          onChange={onQuery}
          placeholder="Buscar hojas"
          label="Buscar hojas"
          shortcut="/"
        />
      </div>
      {sheets.length ? (
        <ul className="sheet-list__items">
          {sheets.map((sheet) => (
            <SheetRow key={sheet.id} sheet={sheet} selected={sheet.id === selectedId} />
          ))}
        </ul>
      ) : (
        <EmptyState
          icon={<Document24Regular />}
          title={
            query ? `Ninguna hoja coincide con '${query}'` : 'No hay hojas visibles para la cuenta del panel'
          }
          actions={
            query ? (
              <Button appearance="secondary" onClick={() => onQuery('')}>
                Borrar búsqueda
              </Button>
            ) : undefined
          }
        />
      )}
    </section>
  )
}

function SheetRow({ sheet, selected }: { sheet: Sheet; selected: boolean }) {
  return (
    <li>
      <Link className="sheet-row" data-selected={selected} to={sheetPath(sheet.id)}>
        <span className="sheet-row__name" title={sheet.name}>
          {sheet.name}
        </span>
        <span className="sheet-row__meta">
          {sheet.modifiedAt ? formatRelativeTime(sheet.modifiedAt) : 'Fecha no disponible'}
        </span>
        <span className="sheet-row__badges">
          {!sheet.inMyList && (
            <Badge tone="warning">De otra persona{sheet.ownerEmail ? `: ${sheet.ownerEmail}` : ''}</Badge>
          )}
          {sheet.inMyList && !sheet.canManageShares && <Badge>Solo lectura</Badge>}
          {sheet.hasDynamicView && <Badge tone="info">Vista dinámica</Badge>}
        </span>
      </Link>
    </li>
  )
}

function SheetListSkeleton() {
  return (
    <section className="sheet-list" aria-busy="true">
      <header className="sheet-list__header">
        <Skeleton variant="title" />
      </header>
      {Array.from({ length: 10 }, (_, index) => (
        <div className="sheet-list__skeleton" key={index}>
          <Skeleton />
          <Skeleton />
        </div>
      ))}
    </section>
  )
}
