import {
  Checkmark16Regular,
  Copy16Regular,
  Copy24Regular,
  DocumentText20Regular,
} from '@fluentui/react-icons'
import { useState } from 'react'
import { Badge, Button, DataTable } from '../../components/ui'
import { ospRowText, ospTableText, turnpikeText } from './lib/ospRow'
import type { WorkLocation } from './types'

// Encabezado corto para el panel angosto y, en `title`, el nombre de la columna en OSP.
const columns = [
  ['County', 'County'],
  ['State Road ID', 'State Road ID'],
  ['Section', 'Section Number'],
  ['Begin MP', 'Beginning Milepost'],
  ['End MP', 'Ending Milepost'],
  ['Turnpike', 'Is Location on Turnpike?'],
]

function CopyRowButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
  }
  return (
    <Button
      appearance="subtle"
      size="sm"
      iconOnly
      aria-label={label}
      title={label}
      onClick={() => void copy()}
    >
      {copied ? <Checkmark16Regular aria-hidden="true" /> : <Copy16Regular aria-hidden="true" />}
    </Button>
  )
}

/** Tabla Work Location de OSP: una fila por vía del trazo, lista para copiar (PEN-32). */
export function WorkLocationTable({ rows }: { rows: WorkLocation[] }) {
  const [copied, setCopied] = useState(false)
  const copyTable = async () => {
    await navigator.clipboard.writeText(ospTableText(rows))
    setCopied(true)
  }
  return (
    <section className="map-result-section">
      <h2>
        <DocumentText20Regular aria-hidden="true" />
        Work Location (como en OSP)
      </h2>
      <DataTable caption="Work Location: una fila por cada vía del trazo">
        <thead>
          <tr>
            {columns.map(([label, title]) => (
              <th key={label} scope="col" title={title}>
                {label}
              </th>
            ))}
            <th scope="col">
              <span className="sr-only">Copiar</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.roadwayId}-${index}`}>
              <td>{row.county ?? '—'}</td>
              <td className="map-table__road">
                <strong>{row.stateRoadId}</strong>
                {row.kind !== 'state' && <Badge tone="warning">No estatal</Badge>}
                {row.localName && <small>{row.localName}</small>}
              </td>
              <td>{row.sectionNumber ?? '—'}</td>
              <td>{row.beginningMilepost.toFixed(3)}</td>
              <td>{row.endingMilepost.toFixed(3)}</td>
              <td>{turnpikeText(row.onTurnpike) || '—'}</td>
              <td>
                <CopyRowButton text={ospRowText(row)} label={`Copiar fila de ${row.stateRoadId}`} />
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      <Button appearance="secondary" onClick={() => void copyTable()}>
        <Copy24Regular aria-hidden="true" />
        {copied ? 'Tabla copiada' : 'Copiar tabla para Excel o Smartsheet'}
      </Button>
    </section>
  )
}
