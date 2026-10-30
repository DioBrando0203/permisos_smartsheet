import { http, HttpResponse } from 'msw'
import { mapPointFixture, mapSearchFixture, mapSegmentFixture } from '../fixtures/map'

export const mapHandlers = [
  http.get('/api/map/search', () => HttpResponse.json(mapSearchFixture)),
  http.get('/api/map/point', () => HttpResponse.json(mapPointFixture)),
  http.get('/api/map/segment', () => HttpResponse.json(mapSegmentFixture)),
]
