type Props = { value: number; max: number; label: string }

export function MeterBar({ value, max, label }: Props) {
  const percent = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="meter-bar">
      <div
        className="meter-bar__track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value}
      >
        <span style={{ width: `${percent}%` }} />
      </div>
      <span>
        {label}: {value}
      </span>
    </div>
  )
}
