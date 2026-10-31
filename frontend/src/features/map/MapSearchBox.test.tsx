import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { mapCrossingFixture } from '../../test/fixtures/map'
import { server } from '../../test/server'
import type { MapScope } from './area'
import { MapSearchBox } from './MapSearchBox'

const allFlorida: MapScope = { county: null, city: null }

function renderBox(scope = allFlorida) {
  const onSelect = vi.fn()
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MapSearchBox scope={scope} onSelect={onSelect} />
    </QueryClientProvider>,
  )
  return onSelect
}

describe('MapSearchBox', () => {
  it('sugiere resultados con su tipo y elige con el teclado', async () => {
    const user = userEvent.setup()
    const onSelect = renderBox()
    await user.type(screen.getByRole('combobox', { name: 'Buscar lugar' }), 'SR 953 3.5')
    const option = await screen.findByRole('option', { name: /SR 953 · MP 3.500/ })
    expect(option).toHaveTextContent('Ruta y milepost · Miami-Dade · vía 87281000')
    expect(screen.getByRole('status')).toHaveTextContent('No respondió: direcciones y cruces (Censo).')
    await user.keyboard('{ArrowDown}{Enter}')
    expect(onSelect).toHaveBeenCalledWith({ lat: 25.79, lon: -80.264 }, 'LEJEUNE RD/NW 42 AVE', null)
  })

  it('acepta coordenadas pegadas sin esperar sugerencias', async () => {
    const user = userEvent.setup()
    const onSelect = renderBox()
    await user.type(screen.getByRole('combobox'), '25.771778, -80.263610{Enter}')
    expect(onSelect).toHaveBeenCalledWith({ lat: 25.771778, lon: -80.26361 }, '25.771778, -80.263610', null)
  })

  it('busca el cruce dentro de la ciudad elegida y muestra su milepost', async () => {
    const asked: URL[] = []
    server.use(
      http.get('/api/map/search', ({ request }) => {
        asked.push(new URL(request.url))
        return HttpResponse.json(mapCrossingFixture)
      }),
    )
    const user = userEvent.setup()
    const onSelect = renderBox({ county: 'Broward', city: 'Fort Lauderdale' })
    const street = screen.getByRole('combobox', { name: 'Buscar lugar' })
    expect(street).toHaveAttribute('placeholder', 'Calle o dirección en Fort Lauderdale')
    await user.type(street, 'Las Olas')
    await user.type(screen.getByRole('textbox', { name: 'Cruce con (opcional)' }), '3rd Ave')
    const option = await screen.findByRole('option', { name: /E LAS OLAS BLVD y SE 3 AVE/ })
    expect(option).toHaveTextContent('Cruce · MP 0.258 · Broward · vía 86000142')
    const last = asked[asked.length - 1]
    expect(last.searchParams.get('q')).toBe('Las Olas & 3rd Ave')
    expect(last.searchParams.get('county')).toBe('Broward')
    expect(last.searchParams.get('city')).toBe('Fort Lauderdale')
    await user.keyboard('{Enter}')
    expect(onSelect).toHaveBeenCalledWith(
      { lat: 26.119161, lon: -80.140422 },
      'E LAS OLAS BLVD y SE 3 AVE',
      '86000142',
    )
  })
})
