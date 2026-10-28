import { http, HttpResponse } from 'msw'
import {
  activityFixture,
  auditFixture,
  automationsFixture,
  contactsFixture,
  groupsFixture,
  sharesFixture,
  sheetsFixture,
} from '../fixtures/sheets'

export const sheetHandlers = [
  http.get('/api/sheets', () => HttpResponse.json(sheetsFixture)),
  http.get('/api/sheets/100', () => HttpResponse.json(sheetsFixture.sheets[0])),
  http.get('/api/sheets/100/shares', () => HttpResponse.json(sharesFixture)),
  http.get('/api/sheets/100/audit', () => HttpResponse.json(auditFixture)),
  http.get('/api/sheets/100/activity', () => HttpResponse.json(activityFixture)),
  http.get('/api/sheets/100/automations', () => HttpResponse.json(automationsFixture)),
  http.get('/api/contacts', () => HttpResponse.json(contactsFixture)),
  http.get('/api/groups', () => HttpResponse.json(groupsFixture)),
]
