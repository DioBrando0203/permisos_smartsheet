import { lazy, Suspense } from 'react'
import { Spinner } from '../../components/ui'

const MapPage = lazy(() => import('./MapPage').then((module) => ({ default: module.MapPage })))

export function MapRoute() {
  return (
    <Suspense
      fallback={
        <div className="shell-loading">
          <Spinner label="Cargando mapa" />
        </div>
      }
    >
      <MapPage />
    </Suspense>
  )
}
