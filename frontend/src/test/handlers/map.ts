import { http, HttpResponse } from 'msw'
import { mapPointFixture, mapSearchFixture, mapTraceFixture, parcelOutlinesFixture } from '../fixtures/map'

export const mapHandlers = [
  http.get('/api/map/search', () => HttpResponse.json(mapSearchFixture)),
  http.get('/api/map/point', () => HttpResponse.json(mapPointFixture)),
  http.get('/api/map/trace', () => HttpResponse.json(mapTraceFixture)),
  http.get('/api/map/parcels', () => HttpResponse.json(parcelOutlinesFixture)),
]
