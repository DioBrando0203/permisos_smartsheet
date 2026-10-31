import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { MapScope } from './area'
import { MapScopePicker } from './MapScopePicker'

function renderPicker(scope: MapScope) {
  const onScope = vi.fn()
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MapScopePicker scope={scope} onScope={onScope} />
    </QueryClientProvider>,
  )
  return onScope
}

describe('MapScopePicker', () => {
  it('pone primero los condados donde trabaja el equipo', async () => {
    const user = userEvent.setup()
    const onScope = renderPicker({ county: null, city: null })
    const county = screen.getByRole('combobox', { name: 'Condado' })
    const featured = await screen.findByRole('group', { name: 'Donde trabajamos' })
    expect(
      within(featured)
        .getAllByRole('option')
        .map((option) => option.textContent),
    ).toEqual(['Broward', 'Miami-Dade'])
    expect(screen.getByRole('combobox', { name: 'Ciudad' })).toBeDisabled()
    await user.selectOptions(county, 'Broward')
    expect(onScope).toHaveBeenCalledWith({ county: 'Broward', city: null })
  })

  it('lista sólo los municipios del condado y elige uno', async () => {
    const user = userEvent.setup()
    const onScope = renderPicker({ county: 'Broward', city: null })
    const city = screen.getByRole('combobox', { name: 'Ciudad' })
    await screen.findByRole('option', { name: 'Fort Lauderdale' })
    expect(
      within(city)
        .getAllByRole('option')
        .map((option) => option.textContent),
    ).toEqual(['Todo el condado', 'Fort Lauderdale', 'Hollywood'])
    await user.selectOptions(city, 'Fort Lauderdale')
    expect(onScope).toHaveBeenCalledWith({ county: 'Broward', city: 'Fort Lauderdale' })
  })
})
