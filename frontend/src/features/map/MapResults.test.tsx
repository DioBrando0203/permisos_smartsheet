import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { mapPointFixture, mapSegmentFixture } from '../../test/fixtures/map'
import { PointResult, SegmentResult } from './MapResults'
import { normalizeMapPoint, normalizeMapSegment } from './normalize'

const noop = () => undefined

describe('Resultados del mapa', () => {
  it('muestra el punto con etiquetas, botones de copiar y fuentes legibles', () => {
    render(
      <PointResult result={normalizeMapPoint(mapPointFixture)} loading={false} error={null} onRetry={noop} />,
    )
    expect(screen.getByText('SR 953')).toBeInTheDocument()
    expect(screen.getByText('Vía estatal')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Copiar milepost' })).toBeInTheDocument()
    expect(screen.getByText('FDOT (Estado de Florida)')).toBeInTheDocument()
    expect(screen.getByText('Confianza alta')).toBeInTheDocument()
    expect(screen.getByText('Miami-Dade')).toBeInTheDocument()
    expect(screen.getByText('PROPIETARIO SINTETICO 1')).toBeInTheDocument()
    expect(screen.getByText('Otras vías cerca (1)')).toBeInTheDocument()
    expect(screen.getByText('Fuentes: 1 de 2 respondieron')).toBeInTheDocument()
    expect(screen.getByText(/Parcelas \(FDACS\)/)).toHaveTextContent('no respondió')
  })

  it('da cada campo de OSP con su botón y copia la fila tabulada', async () => {
    const user = userEvent.setup()
    render(
      <SegmentResult
        result={normalizeMapSegment(mapSegmentFixture)}
        loading={false}
        error={null}
        waiting={false}
        onRetry={noop}
      />,
    )
    for (const field of [
      'County',
      'State Road ID',
      'Section Number',
      'Beginning Milepost',
      'Ending Milepost',
    ])
      expect(screen.getByRole('button', { name: `Copiar ${field}` })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Copiar fila para Excel o Smartsheet' }))
    expect(await navigator.clipboard.readText()).toBe('Miami-Dade\t87281000\t281\t3.124\t3.839')
    expect(screen.getByRole('button', { name: 'Fila copiada' })).toBeInTheDocument()
  })
})
