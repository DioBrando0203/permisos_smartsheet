import { describe, expect, it } from 'vitest'
import type { Person } from '../../../lib/types'
import { filterPeople } from './filterPeople'

const people: Person[] = [
  {
    key: 'org@example.com',
    type: 'USER',
    name: 'Org',
    email: 'org@example.com',
    sheetCount: 2,
    highestLevel: 'EDITOR',
    isContact: true,
    isOrgMember: true,
    isTokenOwner: false,
    lastLogin: null,
  },
  {
    key: 'external@example.com',
    type: 'USER',
    name: 'External',
    email: 'external@example.com',
    sheetCount: 1,
    highestLevel: 'VIEWER',
    isContact: false,
    isOrgMember: false,
    isTokenOwner: false,
    lastLogin: null,
  },
  {
    key: 'group-1',
    type: 'GROUP',
    name: 'Grupo',
    email: null,
    sheetCount: 3,
    highestLevel: 'ADMIN',
    isContact: false,
    isOrgMember: false,
    isTokenOwner: false,
    lastLogin: null,
  },
]

describe('filterPeople', () => {
  it('filtra usuarios externos sin incluir grupos', () => {
    expect(filterPeople(people, 'external', '').map((person) => person.key)).toEqual(['external@example.com'])
  })

  it('ordena por cantidad de hojas', () => {
    expect(filterPeople(people, 'all', '').map((person) => person.key)).toEqual([
      'group-1',
      'org@example.com',
      'external@example.com',
    ])
  })
})
