import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MapSearchBox } from './MapSearchBox'

function renderBox() {
  const onSelect = vi.fn()
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MapSearchBox onSelect={onSelect} />
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
    expect(screen.getByRole('status')).toHaveTextContent('No respondió: direcciones (Censo).')
    await user.keyboard('{ArrowDown}{Enter}')
    expect(onSelect).toHaveBeenCalledWith({ lat: 25.79, lon: -80.264 }, 'LEJEUNE RD/NW 42 AVE')
  })

  it('acepta coordenadas pegadas sin esperar sugerencias', async () => {
    const user = userEvent.setup()
    const onSelect = renderBox()
    await user.type(screen.getByRole('combobox'), '25.771778, -80.263610{Enter}')
    expect(onSelect).toHaveBeenCalledWith({ lat: 25.771778, lon: -80.26361 }, '25.771778, -80.263610')
  })
})
