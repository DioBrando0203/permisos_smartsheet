import {
  ClipboardTaskListLtr24Regular,
  DocumentMultiple24Regular,
  People24Regular,
  PersonStarburst24Regular,
  ScaleFill24Regular,
} from '@fluentui/react-icons'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router'
import type { Me } from '../../lib/types'

const destinations = [
  { to: '/hojas', label: 'Hojas', icon: DocumentMultiple24Regular },
  { to: '/personas', label: 'Personas', icon: People24Regular },
  { to: '/disenadores', label: 'Diseñadores', icon: PersonStarburst24Regular },
  { to: '/revision', label: 'Revisión', icon: ClipboardTaskListLtr24Regular },
  { to: '/comparar', label: 'Comparar', icon: ScaleFill24Regular },
]

type Props = { me: Me | null; readOnly: boolean; children: ReactNode }

export function AppLayout({ me, readOnly, children }: Props) {
  return (
    <div className="app-layout">
      <a className="skip-link" href="#main-content">
        Saltar al contenido
      </a>
      <header className="app-layout__header">
        <strong>Permisos de Smartsheet</strong>
        <span>{me?.accountName || 'Cuenta de Smartsheet'}</span>
        <span>{me?.name || me?.email || 'Cargando cuenta…'}</span>
      </header>
      {readOnly && (
        <div className="read-only-banner" role="status">
          Modo solo lectura: el panel no cambia nada en Smartsheet.
        </div>
      )}
      <nav className="app-layout__nav" aria-label="Principal">
        {destinations.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `app-layout__nav-link${isActive ? ' active' : ''}`}
            title={label}
          >
            <Icon aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <main id="main-content" className="app-layout__content">
        {children}
      </main>
    </div>
  )
}
