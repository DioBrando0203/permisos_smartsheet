import type { WorkLocation } from '../types'

/** Columnas de Work Location en OSP, en su orden e idioma, para pegar en una tabla. */
export const ospHeaders = [
  'County',
  'State Road ID',
  'Section Number',
  'Beginning Milepost',
  'Ending Milepost',
  'Is Location on Turnpike?',
]

/** Como OSP: "Yes" o "No"; vacío si no se pudo consultar el Turnpike. */
export function turnpikeText(value: boolean | null): string {
  return value === null ? '' : value ? 'Yes' : 'No'
}

export function ospCells(row: WorkLocation): string[] {
  return [
    row.county ?? '',
    row.stateRoadId,
    row.sectionNumber ?? '',
    row.beginningMilepost.toFixed(3),
    row.endingMilepost.toFixed(3),
    turnpikeText(row.onTurnpike),
  ]
}

export function ospRowText(row: WorkLocation): string {
  return ospCells(row).join('\t')
}

/** Tabla con encabezados, separada por tabulaciones, para Excel o Smartsheet. */
export function ospTableText(rows: WorkLocation[]): string {
  return [ospHeaders, ...rows.map(ospCells)].map((cells) => cells.join('\t')).join('\n')
}
