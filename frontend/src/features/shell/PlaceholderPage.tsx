import { WrenchScrewdriver24Regular } from '@fluentui/react-icons'
import { EmptyState } from '../../components/ui'

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <EmptyState icon={<WrenchScrewdriver24Regular />} title={`${title}: próximamente`}>
      <p>Esta vista se incorpora en una fase posterior.</p>
    </EmptyState>
  )
}
