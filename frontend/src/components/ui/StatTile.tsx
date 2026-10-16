type Props = { label: string; value: string | number }

export function StatTile({ label, value }: Props) {
  return (
    <section className="stat-tile">
      <strong>{value}</strong>
      <span>{label}</span>
    </section>
  )
}
