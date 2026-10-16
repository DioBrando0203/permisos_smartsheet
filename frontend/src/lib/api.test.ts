import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { api } from './api'
import { normalizeHealth } from './normalize'
import { server } from '../test/server'

describe('api', () => {
  it('lee y normaliza el estado de salud mediante MSW', async () => {
    const result = await api<{ status: string; smartsheet: string; read_only: boolean }>('/api/health')
    expect(normalizeHealth(result)).toEqual({ status: 'ok', smartsheet: 'configured', readOnly: true })
  })

  it('convierte un error conocido del backend en ApiError', async () => {
    server.use(
      http.get('/api/health', () =>
        HttpResponse.json(
          { detail: { code: 'SMARTSHEET_RATE_LIMITED', message: 'Demasiadas solicitudes', ref_id: 'abc' } },
          { status: 503 },
        ),
      ),
    )
    await expect(api('/api/health')).rejects.toMatchObject({
      code: 'SMARTSHEET_RATE_LIMITED',
      message: 'Demasiadas solicitudes',
      refId: 'abc',
      status: 503,
    })
  })

  it('convierte una respuesta 422 de FastAPI en VALIDATION', async () => {
    server.use(http.get('/api/health', () => HttpResponse.json({ detail: [] }, { status: 422 })))
    await expect(api('/api/health')).rejects.toMatchObject({ code: 'VALIDATION', status: 422 })
  })

  it('indica cuando el backend no responde', async () => {
    server.use(http.get('/api/health', () => HttpResponse.error()))
    await expect(api('/api/health')).rejects.toMatchObject({ code: 'BACKEND_UNREACHABLE' })
  })
})
