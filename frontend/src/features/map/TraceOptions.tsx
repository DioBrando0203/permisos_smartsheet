import type { TraceOptions as Options } from './lib/mapUrl'

export function TraceOptions({ value, onChange }: { value: Options; onChange: (value: Options) => void }) {
  return (
    <div className="map-toolbar__layer" role="group" aria-label="Ajuste del recorrido">
      <label>
        <input
          type="checkbox"
          checked={value.snap}
          onChange={(event) => onChange({ ...value, snap: event.target.checked })}
        />
        Ajustar a vías (hasta 100 m)
      </label>
      <label>
        <input
          type="checkbox"
          checked={value.original}
          onChange={(event) => onChange({ ...value, original: event.target.checked })}
        />
        Ver dibujo original
      </label>
    </div>
  )
}
