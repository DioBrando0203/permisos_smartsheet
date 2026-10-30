import { createBrowserRouter, Navigate } from 'react-router'
import { App } from './App'
import { SheetsPage } from '../features/sheets/SheetsPage'
import { PlaceholderPage } from '../features/shell/PlaceholderPage'
import { PeoplePage } from '../features/people/PeoplePage'
import { NotFoundPage } from '../features/shell/NotFoundPage'
import { MapRoute } from '../features/map/MapRoute'

export const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/hojas" replace /> },
      { path: '/hojas', element: <SheetsPage /> },
      { path: '/hojas/:sheetId', element: <SheetsPage /> },
      { path: '/personas', element: <PeoplePage /> },
      { path: '/personas/:key', element: <PeoplePage /> },
      { path: '/disenadores', element: <PlaceholderPage title="Diseñadores" /> },
      { path: '/revision', element: <PlaceholderPage title="Revisión" /> },
      { path: '/comparar', element: <PlaceholderPage title="Comparar hojas" /> },
      { path: '/mapa', element: <MapRoute /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
