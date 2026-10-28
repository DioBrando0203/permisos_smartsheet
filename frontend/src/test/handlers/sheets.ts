import { http, HttpResponse } from 'msw'
import { sharesFixture, sheetsFixture } from '../fixtures/sheets'

export const sheetHandlers = [
  http.get('/api/sheets', () => HttpResponse.json(sheetsFixture)),
  http.get('/api/sheets/100', () => HttpResponse.json(sheetsFixture.sheets[0])),
  http.get('/api/sheets/100/shares', () => HttpResponse.json(sharesFixture)),
]
