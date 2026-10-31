import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { mapPointFixture, mapTraceFixture } from '../../test/fixtures/map'
import { PointResult } from './MapResults'
import { normalizeMapPoint, normalizeMapTrace } from './normalize'
import { TraceResult } from './TraceResult'

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
    expect(screen.getByText('Estado').nextElementSibling).toHaveTextContent('Florida')
    expect(screen.getByText('FDACS (datos del tasador)')).toBeInTheDocument()
  })

  it('con FDACS caído en Broward muestra el folio del condado y dice qué falta', () => {
    const fallback = {
      ...mapPointFixture,
      parcel: { parcel_id: '000000000002', county_code_dor: '16', source: 'broward_parcels' },
      sources: [
        { id: 'fdacs_parcels', status: 'timeout' as const, ms: 5000 },
        { id: 'broward_parcels', status: 'ok' as const, ms: 900 },
      ],
    }
    render(<PointResult result={normalizeMapPoint(fallback)} loading={false} error={null} onRetry={noop} />)
    expect(screen.getByRole('button', { name: 'Copiar parcela' })).toBeInTheDocument()
    expect(screen.getByText('000000000002')).toBeInTheDocument()
    expect(screen.getByText('Condado de Broward (sólo el folio)')).toBeInTheDocument()
    expect(screen.getByText('Propietario (tasador)').nextElementSibling).toHaveTextContent('No disponible')
    expect(screen.getByText(/Parcelas de Broward \(condado\)/)).not.toHaveTextContent('no respondió')
  })

  it('el trazo da la tabla Work Location de OSP y copia fila o tabla (PEN-32)', async () => {
    const user = userEvent.setup()
    render(<TraceResult {...traceProps} result={normalizeMapTrace(mapTraceFixture)} />)
    const [, first, second] = screen.getAllByRole('row')
    expect(first).toHaveTextContent('Miami-DadeSR 953LEJEUNE RD/NW 42 AVE2813.1243.839No')
    expect(second).toHaveTextContent('No estatal')
    expect(screen.getByText(/Recorrido sobre geometría FDOT/)).toBeInTheDocument()
    expect(screen.getByText('Línea marcada: 0.920 mi.')).toBeInTheDocument()
    expect(
      screen.getByText(/Distancia de los extremos a la vía: inicio 5.5 m; final 8.1 m/),
    ).toBeInTheDocument()
    expect(screen.getByText('Dibujo asociado a vías: 100.0 % (estimado).')).toBeInTheDocument()
    expect(screen.getByText(/no es del Sistema Estatal/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Copiar fila de SR 953' }))
    expect(await navigator.clipboard.readText()).toBe('Miami-Dade\tSR 953\t281\t3.124\t3.839\tNo')
    await user.click(screen.getByRole('button', { name: 'Copiar tabla para Excel o Smartsheet' }))
    expect((await navigator.clipboard.readText()).split('\n')).toHaveLength(3)
    expect(screen.getByRole('button', { name: 'Tabla copiada' })).toBeInTheDocument()
  })

  it('mientras se dibuja sólo deja terminar con dos puntos o más', async () => {
    const user = userEvent.setup()
    const onFinish = vi.fn()
    const { rerender } = render(<TraceResult {...traceProps} drawing vertices={1} onFinish={onFinish} />)
    expect(screen.getByRole('button', { name: 'Terminar' })).toBeDisabled()
    rerender(<TraceResult {...traceProps} drawing vertices={3} onFinish={onFinish} />)
    await user.click(screen.getByRole('button', { name: 'Terminar' }))
    expect(onFinish).toHaveBeenCalledOnce()
    expect(screen.getByText('3 puntos')).toBeInTheDocument()
  })

  it('explica huecos y una longitud desconocida sin mostrar cero', () => {
    const result = normalizeMapTrace({
      ...mapTraceFixture,
      length_mi: null,
      matched_percent: 60,
      unmatched_length_mi: 0.1,
      warnings: ['TRACE_PARTIAL', 'TRACE_GEOMETRY_INCOMPLETE'],
    })
    render(<TraceResult {...traceProps} result={result} />)
    expect(screen.getByText('Revisar recorrido incompleto')).toBeInTheDocument()
    expect(screen.getByText(/161 m del dibujo quedan sin vía/)).toBeInTheDocument()
    expect(screen.getByText('Geometría de vía incompleta')).toBeInTheDocument()
    expect(screen.getByText(/Longitud no disponible sobre/)).toBeInTheDocument()
    expect(screen.queryByText(/0.000 mi/)).not.toBeInTheDocument()
  })

  it('identifica el recorrido reconstruido y advierte alternativas y conexiones geométricas', () => {
    const result = normalizeMapTrace({
      ...mapTraceFixture,
      alignment: 'ambiguous',
      radius_m: 100,
      snapped_points: [
        [25.771778, -80.26361],
        [25.782147, -80.264005],
      ],
      warnings: ['TRACE_ALIGNMENT_AMBIGUOUS', 'TRACE_CONNECTIONS_INFERRED'],
    })
    render(<TraceResult {...traceProps} result={result} />)
    expect(screen.getByText(/Recorrido reconstruido sobre las vías/)).toBeInTheDocument()
    expect(screen.getByText('Hay recorridos alternativos similares')).toBeInTheDocument()
    expect(screen.getByText(/Revisa cruces a desnivel/)).toBeInTheDocument()
    expect(result.snappedPoints[1]).toEqual({ lat: 25.782147, lon: -80.264005 })
  })
})

const traceProps = {
  vertices: 2,
  drawing: false,
  loading: false,
  error: null,
  onFinish: noop,
  onUndo: noop,
  onClear: noop,
  onRetry: noop,
}

describe('Vía preferida', () => {
  it('pone primero la vía del resultado elegido en el buscador', () => {
    render(
      <PointResult
        result={normalizeMapPoint(mapPointFixture)}
        loading={false}
        error={null}
        onRetry={() => undefined}
        preferRoadway="87053000"
      />,
    )
    expect(screen.getByText('SR 968')).toBeInTheDocument()
    expect(screen.getByText('Otras vías cerca (1)')).toBeInTheDocument()
  })
})
