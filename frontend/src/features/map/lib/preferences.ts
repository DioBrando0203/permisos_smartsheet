/** Preferencias de vista del mapa en localStorage: sólo opciones, nunca datos (ADR-05). */
export function readChoice<T extends string>(key: string, choices: readonly T[], fallback: T): T {
  try {
    const saved = localStorage.getItem(key)
    return choices.find((choice) => choice === saved) ?? fallback
  } catch {
    return fallback
  }
}

export function saveChoice(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Sin almacenamiento (modo privado): sólo se pierde la preferencia.
  }
}

/** Texto libre guardado (condado o ciudad elegidos); vacío o sin almacenamiento da null. */
export function readText(key: string): string | null {
  try {
    return localStorage.getItem(key) || null
  } catch {
    return null
  }
}
