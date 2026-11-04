import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, renderHook, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { server } from '../../test/server'
import { normalizeTraceStreets, type ApiTraceStreets } from './streets'
import { TraceStreetsSection } from './TraceStreets'
import { useStreetLayer } from './useStreetLayer'

const noop = () => undefined
const trace: ApiTraceStreets = {
  county: 'St. Johns',
  source: 'stjohns_roads',
  streets: [
    {
      name: 'County Road 210 W',
      maintainer: 'St Johns County',
      authority: 'COUNTY',
      authority_name: 'St. Johns County',
      length_mi: 0.476,
      paths: [],
    },
    { name: 'Synthetic Ln', maintainer: 'Proposed', authority: null, length_mi: 0.05, paths: [] },
  ],
  unmatched_length_mi: 0.036,
  sources: [{ id: 'stjohns_roads', status: 'ok', ms: 900 }],
  warnings: ['TRACE_PARTIAL'],
}

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('Calles y permisos del trazo (PEN-41)', () => {
  it('lista las calles en orden con responsable, longitud y permiso, y copia la lista', async () => {
    const user = userEvent.setup()
    const write = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue()
    render(
      <TraceStreetsSection
        result={normalizeTraceStreets(trace)}
        loading={false}
        error={null}
        onRetry={noop}
      />,
    )
    const [first, second] = screen.getAllByRole('listitem')
    expect(first).toHaveTextContent('County Road 210 W0.476 mi')
    expect(first).toHaveTextContent('Permiso de uso del derecho de vía de St. Johns County.')
    expect(second).toHaveTextContent('El condado no dice quién la mantiene («Proposed»)')
    expect(screen.getByText('Sin calle del condado: 0.036 mi del dibujo.')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Copiar lista para Excel o Smartsheet' }))
    expect(write.mock.calls[0]?.[0]).toMatch(/^Calle\tMantenimiento/)
    expect(screen.getByRole('button', { name: 'Lista copiada' })).toBeInTheDocument()
  })

  it('fuera de St. Johns lo dice en una línea', () => {
    const outside = normalizeTraceStreets({ streets: [], warnings: ['NO_COUNTY_SOURCE'] })
    render(<TraceStreetsSection result={outside} loading={false} error={null} onRetry={noop} />)
    expect(
      screen.getByText('Por ahora sólo St. Johns publica quién mantiene cada calle.'),
    ).toBeInTheDocument()
  })

  it('la capa pide celdas de 0.02 grados desde el zoom 15 y colorea por responsable', async () => {
    const cells: string[] = []
    server.use(
      http.get('/api/map/streets', ({ request }) => {
        cells.push(new URL(request.url).search)
        return HttpResponse.json({
          source: 'stjohns_roads',
          county: 'St. Johns',
          streets: [
            {
              id: '1',
              name: 'Beachwalk Blvd',
              maintainer: 'St Johns County',
              authority: 'COUNTY',
              paths: [
                [
                  [-81.47, 30.08],
                  [-81.46, 30.09],
                ],
              ],
            },
          ],
        })
      }),
    )
    const bounds = { west: -81.479, south: 30.081, east: -81.461, north: 30.099 }
    const far = renderHook(() => useStreetLayer(true, { bounds, zoom: 14 }), { wrapper })
    expect(far.result.current.hint).toMatch(/Acércate \(zoom 15/)
    const near = renderHook(() => useStreetLayer(true, { bounds, zoom: 15 }), { wrapper })
    await waitFor(() => expect(near.result.current.overlays).toHaveLength(1))
    expect(cells).toEqual(['?west=-81.48&south=30.08&east=-81.46&north=30.1'])
    expect(near.result.current.overlays[0]?.className).toBe('map-street street-tone--county')
    expect(near.result.current.tones).toEqual(['county'])
    expect(near.result.current.hint).toBeNull()
  })
})
