import { ArrowDownload20Regular, Person24Regular } from '@fluentui/react-icons'
import { Link } from 'react-router'
import {
  Avatar,
  Badge,
  Button,
  EmptyState,
  LoadingNotice,
  SearchBox,
  Skeleton,
  StatusAlert,
} from '../../components/ui'
import { accessLevels } from '../../lib/accessLevels'
import { errorMessage } from '../../lib/errorMessages'
import { formatRelativeTime } from '../../lib/formatters'
import { personPath } from '../../lib/routes'
import type { Person } from '../../lib/types'
import { filterPeople, type PeopleFilter } from './lib/filterPeople'

const filters: { id: PeopleFilter; label: string }[] = [
  { id: 'all', label: 'Todos' },
  { id: 'with_access', label: 'Con acceso' },
  { id: 'without_access', label: 'Sin acceso' },
  { id: 'org', label: 'Organización' },
  { id: 'external', label: 'Externos' },
  { id: 'contacts', label: 'Contactos' },
  { id: 'groups', label: 'Grupos' },
]

type Props = {
  people: Person[]
  total: number
  loading: boolean
  error: Error | null
  filter: PeopleFilter
  query: string
  incomplete: boolean
  failed: number
  onFilter: (filter: PeopleFilter) => void
  onQuery: (query: string) => void
  onRetry: () => void
}

export function PeopleList({
  people,
  total,
  loading,
  error,
  filter,
  query,
  incomplete,
  failed,
  onFilter,
  onQuery,
  onRetry,
}: Props) {
  if (loading) return <PeopleListSkeleton />
  if (error)
    return (
      <StatusAlert tone="error" title="No se pudieron cargar las personas">
        {errorMessage('BACKEND_UNREACHABLE', error.message).text}{' '}
        <Button appearance="subtle" onClick={onRetry}>
          Reintentar
        </Button>
      </StatusAlert>
    )
  const filtered = filterPeople(people, filter, query)
  return (
    <section className="people-list">
      <header>
        <div>
          <h1>Personas</h1>
          <span role="status">
            {filtered.length} de {total} personas
          </span>
        </div>
        <a
          className="button button--secondary button--sm"
          href="/api/export/access.csv"
          download
          title="Incluye correos reales: compártalo sólo con quien lo necesite"
        >
          <ArrowDownload20Regular aria-hidden="true" />
          Exportar a Excel
        </a>
      </header>
      {incomplete && (
        <StatusAlert tone="warning" title={`No se pudieron leer ${failed} hojas`}>
          Se muestran los datos que sí se pudieron cargar.
        </StatusAlert>
      )}
      <div className="people-list__filters">
        <label>
          Filtro
          <select value={filter} onChange={(event) => onFilter(event.target.value as PeopleFilter)}>
            {filters.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <SearchBox
          value={query}
          onChange={onQuery}
          placeholder="Buscar personas"
          label="Buscar personas"
          shortcut="/"
        />
      </div>
      {filtered.length ? (
        <ul>
          {filtered.map((person) => (
            <li key={person.key}>
              <PersonRow person={person} />
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          icon={<Person24Regular />}
          title={query ? 'Nadie coincide con el filtro' : 'Nadie más tiene acceso a las hojas'}
        />
      )}
    </section>
  )
}

function PersonRow({ person }: { person: Person }) {
  const name = person.name || person.email || 'Sin nombre'
  return (
    <Link className="person-row" to={personPath(person.key)}>
      <Avatar name={name} />
      <span>
        <strong>
          {name}
          {person.isTokenOwner && ' (usted)'}
        </strong>
        {person.email && <small>{person.email}</small>}
        <small>
          {person.sheetCount} hojas{person.highestLevel && ` · ${accessLevels[person.highestLevel].label}`}
        </small>
        {person.lastLogin && <small>Última conexión {formatRelativeTime(person.lastLogin)}</small>}
      </span>
      <span className="person-row__badges">
        {person.isOrgMember && <Badge>Organización</Badge>}
        {person.isContact && <Badge tone="info">Contacto</Badge>}
        {person.type === 'GROUP' && <Badge>Grupo</Badge>}
      </span>
    </Link>
  )
}

function PeopleListSkeleton() {
  return (
    <section className="people-list" aria-busy="true">
      <LoadingNotice>Leyendo permisos de todas las hojas…</LoadingNotice>
      {Array.from({ length: 8 }, (_, index) => (
        <div className="people-list__skeleton" key={index}>
          <Skeleton variant="avatar" />
          <Skeleton />
        </div>
      ))}
    </section>
  )
}
