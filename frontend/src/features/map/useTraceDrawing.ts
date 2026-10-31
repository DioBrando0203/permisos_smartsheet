import { useRef, useState } from 'react'
import type { Coordinates } from './lib/coordinates'

// El doble clic llega como dos clics más el doble clic: los puntos casi iguales se descartan.
const repeatMeters = 2

function meters(a: Coordinates, b: Coordinates): number {
  const y = (b.lat - a.lat) * 111_320
  const x = (b.lon - a.lon) * 111_320 * Math.cos((a.lat * Math.PI) / 180)
  return Math.hypot(x, y)
}

function withoutRepeats(points: Coordinates[]): Coordinates[] {
  return points.filter((point, index) => index === 0 || meters(points[index - 1], point) > repeatMeters)
}

/**
 * Vértices del trazo, como en OSP (PEN-32): cada clic agrega uno; doble clic, Enter o
 * "Terminar" lo cierran; terminado, el siguiente clic empieza otro.
 */
export function useTraceDrawing(initial: Coordinates[] | null) {
  const [vertices, setVertices] = useState<Coordinates[]>(initial ?? [])
  const [finished, setFinished] = useState<Coordinates[] | null>(initial)
  // Copia síncrona: el doble clic llega antes de que React vuelva a dibujar tras los clics.
  const latest = useRef({ vertices: initial ?? [], finished: initial })
  const update = (next: Coordinates[], done: Coordinates[] | null) => {
    latest.current = { vertices: next, finished: done }
    setVertices(next)
    setFinished(done)
  }
  const add = (point: Coordinates) => {
    const { vertices: current, finished: done } = latest.current
    update(done ? [point] : [...current, point], null)
  }
  const finish = () => {
    const path = withoutRepeats(latest.current.vertices)
    update(path, path.length >= 2 ? path : null)
  }
  const undo = () => update(latest.current.vertices.slice(0, -1), null)
  const clear = () => update([], null)
  return { vertices, finished, drawing: !finished, add, finish, undo, clear }
}
