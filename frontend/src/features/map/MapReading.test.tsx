import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { mapPointFixture, mapTraceFixture } from '../../test/fixtures/map'
import { server } from '../../test/server'
import { useMapPoint, useMapTrace } from './hooks'

function queryWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>
  }
}

describe('Actualizar mapa', () => {
  it('punto y trazo saltan la caché del backend con refresh=true', async () => {
    const calls: string[] = []
    server.use(
      http.get('/api/map/point', ({ request }) => {
        calls.push(request.url)
        return HttpResponse.json(mapPointFixture)
      }),
      http.get('/api/map/trace', ({ request }) => {
        calls.push(request.url)
        return HttpResponse.json(mapTraceFixture)
      }),
    )
    const wrapper = queryWrapper()
    const point = renderHook(() => useMapPoint({ lat: 25.77, lon: -80.26 }), { wrapper })
    const trace = renderHook(
      () =>
        useMapTrace([
          { lat: 25.77, lon: -80.26 },
          { lat: 25.78, lon: -80.26 },
        ]),
      { wrapper },
    )
    await waitFor(() => {
      expect(point.result.current.data).toBeDefined()
      expect(trace.result.current.data).toBeDefined()
    })
    act(() => {
      point.result.current.refresh()
      trace.result.current.refresh()
    })
    await waitFor(() => expect(calls.filter((url) => url.includes('refresh=true'))).toHaveLength(2))
    expect(calls.find((url) => url.includes('/trace?'))).toContain('snap=true&radius_m=100')
  })

  it('un error de actualización se muestra aunque haya datos anteriores', async () => {
    const point = renderHook(() => useMapPoint({ lat: 25.77, lon: -80.26 }), { wrapper: queryWrapper() })
    await waitFor(() => expect(point.result.current.data).toBeDefined())
    server.use(
      http.get('/api/map/point', () =>
        HttpResponse.json(
          { detail: { code: 'GIS_UNAVAILABLE', message: 'La fuente no respondió.' } },
          { status: 502 },
        ),
      ),
    )
    act(() => point.result.current.refresh())
    await waitFor(() => expect(point.result.current.error?.message).toBe('La fuente no respondió.'))
    expect(point.result.current.data).toBeDefined()
  })

  it('cambiar ajuste vuelve a consultar sin mezclar las cachés', async () => {
    const asked: URL[] = []
    server.use(
      http.get('/api/map/trace', ({ request }) => {
        asked.push(new URL(request.url))
        return HttpResponse.json(mapTraceFixture)
      }),
    )
    const path = [
      { lat: 25.77, lon: -80.26 },
      { lat: 25.78, lon: -80.26 },
    ]
    const trace = renderHook(({ snap }) => useMapTrace(path, snap), {
      wrapper: queryWrapper(),
      initialProps: { snap: true },
    })
    await waitFor(() => expect(trace.result.current.data).toBeDefined())
    trace.rerender({ snap: false })
    await waitFor(() => expect(asked).toHaveLength(2))
    expect(asked[1].searchParams.get('snap')).toBe('false')
    expect(asked[1].searchParams.get('radius_m')).toBe('25')
  })
})
