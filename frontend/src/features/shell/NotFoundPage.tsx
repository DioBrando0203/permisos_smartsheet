import { Link } from 'react-router'
import { EmptyState } from '../../components/ui'

export function NotFoundPage() {
  return <EmptyState icon="?" title="Esta página no existe" actions={<Link to="/hojas">Ir a Hojas</Link>} />
}
