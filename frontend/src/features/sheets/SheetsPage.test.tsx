import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Outlet, RouterProvider, createMemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { SheetsPage } from './SheetsPage'

function renderPage(initialEntry = '/hojas') {
  const router = createMemoryRouter(
    [
      {
        element: <Outlet context={{ me: null, readOnly: true }} />,
        children: [
          { path: '/hojas', element: <SheetsPage /> },
          { path: '/hojas/:sheetId', element: <SheetsPage /> },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('SheetsPage', () => {
  it('muestra hojas de otras personas y construye su exportación', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Plan 2026')
    await user.selectOptions(screen.getByLabelText('Alcance'), 'others')
    expect(screen.getByText('Ñandú')).toBeInTheDocument()
    expect(screen.getByText(/De otra persona: owner@example.com/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Exportar a Excel/ })).toHaveAttribute(
      'href',
      expect.stringContaining('scope=org_only'),
    )
  })

  it('muestra permisos agrupados al abrir una hoja', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(await screen.findByRole('link', { name: /Plan 2026/ }))
    expect(await screen.findByText('Personas con la hoja compartida')).toBeInTheDocument()
    expect(screen.getByText('Persona Uno')).toBeInTheDocument()
    expect(screen.getAllByText(/Propio|Heredado del workspace/)).toHaveLength(2)
  })
})
