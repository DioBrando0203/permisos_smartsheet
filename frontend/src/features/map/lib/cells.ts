/** Rectángulo en grados (WGS84). */
export type Bounds = { west: number; south: number; east: number; north: number }

/** Lado de cada celda de parcelas (unos 450 m); el backend acepta hasta 0.006 grados. */
export const cellDegrees = 0.004
/** Las parcelas sólo se piden de cerca: a zoom 17 la vista cubre unas seis celdas. */
export const parcelMinZoom = 17
/** Calles por responsable (PEN-41): celdas de unos 2 km; a zoom 15 la vista cubre unas doce. */
export const streetCellDegrees = 0.02
export const streetMinZoom = 15
const maxCells = 24

const round = (value: number) => Number(value.toFixed(6))

/**
 * Celdas fijas de la cuadrícula que cubren la vista. Al mover el mapa se reutilizan las ya
 * pedidas (misma clave de caché); si serían demasiadas, ninguna.
 */
export function cellsFor(view: Bounds, size = cellDegrees): Bounds[] {
  const [x0, x1] = [Math.floor(view.west / size), Math.floor(view.east / size)]
  const [y0, y1] = [Math.floor(view.south / size), Math.floor(view.north / size)]
  if ((x1 - x0 + 1) * (y1 - y0 + 1) > maxCells) return []
  const cells: Bounds[] = []
  for (let x = x0; x <= x1; x++)
    for (let y = y0; y <= y1; y++)
      cells.push({
        west: round(x * size),
        south: round(y * size),
        east: round((x + 1) * size),
        north: round((y + 1) * size),
      })
  return cells
}
