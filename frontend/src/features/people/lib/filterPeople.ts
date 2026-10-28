import { includesSearch } from '../../../lib/search'
import type { Person } from '../../../lib/types'

export type PeopleFilter =
  'all' | 'with_access' | 'without_access' | 'org' | 'external' | 'contacts' | 'groups'

export function filterPeople(people: Person[], filter: PeopleFilter, query: string): Person[] {
  return people
    .filter(
      (person) =>
        matchesFilter(person, filter) && includesSearch(`${person.name ?? ''} ${person.email ?? ''}`, query),
    )
    .sort(
      (a, b) =>
        b.sheetCount - a.sheetCount || (a.name ?? a.email ?? '').localeCompare(b.name ?? b.email ?? '', 'es'),
    )
}

function matchesFilter(person: Person, filter: PeopleFilter): boolean {
  if (filter === 'with_access') return person.sheetCount > 0
  if (filter === 'without_access') return person.sheetCount === 0
  if (filter === 'org') return person.isOrgMember
  if (filter === 'external') return person.type === 'USER' && !person.isOrgMember
  if (filter === 'contacts') return person.isContact
  if (filter === 'groups') return person.type === 'GROUP'
  return true
}
