# SPEC-06 Revisión de la cuenta

Estado: borrador (fase F4)
Responsable del código: `features/review/`, `features/automations/AccountAutomations.tsx`
Relacionadas: backend SPEC-B07, SPEC-B05 (resumen de acceso), SPEC-B10; UX-29, UX-34

## Objetivo

Ver de una vez dónde están los riesgos de toda la cuenta y por dónde empezar a corregir.

## Comportamiento

`/revision` con tres secciones (`?seccion=`): Riesgos (por defecto), Acceso por hoja, Automatizaciones; y Referencias (SPEC-09).

### Riesgos (`GET /api/review?min_severity=`)

1. Selector de severidad mínima: alta, media (por defecto), informativa.
2. StatTiles: hojas revisadas, hojas con alertas, personas por código de alerta.
3. "Personas con más riesgo": tabla de `people` (nombre o correo, alertas, en cuántas hojas) con enlace al detalle de la persona.
4. "Hojas con más riesgo": tabla de `sheets` (nombre, severidad máxima, conteo por alerta) con enlace a la pestaña Auditoría de la hoja.

### Acceso por hoja (`GET /api/sheets/access-summary?q=&inactive_days=`)

1. Buscador (por ejemplo "crown castle") y casilla "Marcar sin cambios en N días" (por defecto 180).
2. Tabla: hoja, personas (sin el propietario), editores, externos, correos personales, inactiva (insignia), con orden por personas.

### Automatizaciones (`GET /api/automations?only_problems=`)

1. StatTiles: hojas con reglas, reglas, funcionan, apagadas, con problemas (`by_status`, `by_problem`).
2. Casilla "Sólo hojas con problemas" (por defecto marcada).
3. Tabla por hoja con conteos y enlace a la pestaña Automatizaciones de la hoja.
4. Primera carga de unos 17 s: LoadingNotice con progreso indeterminado (UX-29).

## Estados

- Carga: esqueleto y LoadingNotice en las cargas largas.
- Vacío: "Sin alertas con esta severidad" / "Sin automatizaciones con problemas".
- Éxito: secciones.
- Parcial: `failed_sheets` como StatusAlert de advertencia con la lista y "Reintentar" (UX-19).
- Error: StatusAlert por sección.

## Criterios de aceptación

- CA-01: cambiar la severidad pide la revisión con el nuevo `min_severity` y conserva la sección. Prueba: componente con MSW.
- CA-02: cada persona y hoja enlaza a su detalle correcto (persona, pestaña Auditoría, pestaña Automatizaciones). Prueba: componente.
- CA-03: una carga de más de 3 s muestra el LoadingNotice y el resto del panel sigue usable. Prueba: componente con respuesta demorada.
- CA-04: `failed_sheets` se muestra junto a los datos leídos. Prueba: componente.
