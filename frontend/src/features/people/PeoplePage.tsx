import { Person24Regular } from '@fluentui/react-icons'
import { useParams, useSearchParams } from 'react-router'
import { EmptyState } from '../../components/ui'
import { PersonDetail } from './PersonDetail'
import { PeopleList } from './PeopleList'
import { usePeople, usePerson } from './hooks'
import { useShellContext } from '../shell/ShellContext'
import type { PeopleFilter } from './lib/filterPeople'

export function PeoplePage() {
  const { key } = useParams()
  const [params, setParams] = useSearchParams()
  const people = usePeople()
  const detail = usePerson(key ?? '')
  const { readOnly } = useShellContext()
  const filter = (params.get('filter') as PeopleFilter | null) ?? 'all'
  const query = params.get('q') ?? ''
  const setValue = (name: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    setParams(next)
  }
  return (
    <div className="people-page">
      <aside className="people-page__list">
        <PeopleList
          people={people.data?.people ?? []}
          total={people.data?.total ?? 0}
          loading={people.isLoading}
          error={people.error}
          filter={filter}
          query={query}
          incomplete={people.data?.incomplete ?? false}
          failed={people.data?.failedSheets.length ?? 0}
          onFilter={(value) => setValue('filter', value === 'all' ? '' : value)}
          onQuery={(value) => setValue('q', value)}
          onRetry={() => void people.refetch()}
        />
      </aside>
      <section className="people-page__detail">
        {key ? (
          <PersonDetail
            key={key}
            loading={detail.isLoading}
            error={detail.error}
            detail={detail.data}
            readOnly={readOnly}
            onRetry={() => void detail.refetch()}
          />
        ) : (
          <EmptyState icon={<Person24Regular />} title="Seleccione una persona">
            <p>Vea las hojas, el nivel más alto y el origen de cada acceso.</p>
          </EmptyState>
        )}
      </section>
    </div>
  )
}
