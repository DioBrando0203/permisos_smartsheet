/** Rectángulo en grados (WGS84). */
export type Bounds = { west: number; south: number; east: number; north: number }

/** Lado de cada celda de parcelas (unos 450 m); el backend acepta hasta 0.006 grados. */
export const cellDegrees = 0.004
/** Las parcelas sólo se piden de cerca: a zoom 17 la vista cubre unas seis celdas. */
export const parcelMinZoom = 17
const maxCells = 24

const round = (value: number) => Number(value.toFixed(6))

/**
 * Celdas fijas de la cuadrícula que cubren la vista. Al mover el mapa se reutilizan las ya
 * pedidas (misma clave de caché); si serían demasiadas, ninguna.
 */
export function cellsFor(view: Bounds): Bounds[] {
  const [x0, x1] = [Math.floor(view.west / cellDegrees), Math.floor(view.east / cellDegrees)]
  const [y0, y1] = [Math.floor(view.south / cellDegrees), Math.floor(view.north / cellDegrees)]
  if ((x1 - x0 + 1) * (y1 - y0 + 1) > maxCells) return []
  const cells: Bounds[] = []
  for (let x = x0; x <= x1; x++)
    for (let y = y0; y <= y1; y++)
      cells.push({
        west: round(x * cellDegrees),
        south: round(y * cellDegrees),
        east: round((x + 1) * cellDegrees),
        north: round((y + 1) * cellDegrees),
      })
  return cells
}
