# Reglas de calidad (frontend)

## Especificación

- C-01: cambio de comportamiento visible implica spec actualizada con criterios de aceptación y su prueba.
- C-02: todo componente que muestre datos remotos define cinco estados: carga, vacío, éxito, parcial y error (UX-16 a UX-19). Si alguno no aplica, la spec lo dice.

## Pruebas

- C-03: lógica pura (`lib/`, `features/*/lib`) con pruebas unitarias de casos normales, bordes y datos ausentes.
- C-04: componentes con React Testing Library por rol y nombre accesible, no por clases CSS.
- C-05: API simulada con MSW en pruebas de componente, con fixtures de la forma del contrato (`src/test/fixtures/`); nunca el backend real ni Smartsheet.
- C-06: E2E con Playwright contra el backend real arrancado con el Smartsheet falso (`backend/tests/fake_smartsheet.py`, ADR-10), nunca contra la cuenta real.
- C-07: fixtures sólo sintéticos (`@example.com`, nombres inventados).
- C-08: cada escritura se prueba en éxito, error del backend y bloqueo por regla (propietario, heredado).

## Revisión visual

- C-09: cambios de UI se revisan en 320, 390, 1024, 1440 y 1920 px con datos extremos: nombre de hoja de 150 caracteres, 200 personas en una hoja, persona sin nombre, correo de 60 caracteres, 0 permisos.
- C-10: `document.documentElement.scrollWidth` no supera `clientWidth` en esos anchos.
- C-11: teclado: Tab en orden lógico, foco visible, Enter y Espacio activan, Esc cierra diálogos.

## Integración

- C-12: antes de integrar pasan `format:check`, `build`, `lint`, `test` y, si cambió flujo o layout, `test:e2e`.
- C-13: RESULTADOS y bitácora reflejan sólo ejecuciones reales, con fecha America/Lima.
- C-14: un bug corregido deja una prueba que habría fallado antes.
- C-15: toda vista con escrituras se prueba también con `read_only: true` (controles deshabilitados con motivo) y con `false`.
- C-16: toda consulta larga se prueba con respuesta demorada (aparece `LoadingNotice`) y con `failed_sheets` (parcial visible).
- C-17: una prueba de contrato por fixture: el fixture pasa por su función de `normalize.ts` sin perder campos; si el backend cambia `API.md`, se actualizan fixture y prueba en el mismo cambio.

