# Plan de calidad (frontend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`. Aún no hay código (F0 pendiente).

## Capas de prueba

- Unitarias (Vitest, sin DOM): `lib/search`, `lib/accessLevels`, `lib/severity`, `lib/errorMessages`, `lib/normalize` (una por endpoint, C-17), `lib/routes`, `lib/formatters`, `features/shares/lib/groupShares` (propio + heredado con el mismo id, B-05), `features/shares/lib/recipients`, extractor de código de permalink (SPEC-07), armado de la query de calidad (SPEC-09), filtros rápidos de personas (SPEC-04).
- Componente (React Testing Library + MSW): una prueba por CA marcado "componente" en SPEC-01 a SPEC-09; cada vista con escrituras en `read_only: true` y `false` (C-15); cada consulta larga con demora y con `failed_sheets` (C-16).
- E2E (Playwright, ADR-10): configuración separada en `playwright.config.ts`, con pruebas en `e2e/` para no mezclar Vitest y Playwright. Desde F7, `webServer` levanta el Smartsheet falso (8791), el GIS falso (8792), el backend de prueba `tests.e2e_backend` apuntado a ambos (8793, solo lectura, sin leer `backend/.env`) y Vite (5791), con el Python de `backend/.venv`; puertos distintos de los de desarrollo y `reuseExistingServer: false`. Teselas y cualquier host externo se bloquean en cada prueba. Hecho: el mapa (`e2e/map.spec.ts`). Pendientes: navegar hojas → detalle → pestañas; persona por URL con `@`; comparar por URL; dar, cambiar y quitar (F5) verificando las escrituras que registró el Smartsheet falso (para F5, `APP_READ_ONLY=false` sólo en el backend de prueba).
- `features/map/lib/traceDisplay.test.ts`: sólo entrega las geometrías LRS al terminar y calcula el rectángulo de todas sus filas (PEN-35); `MapResults.test.tsx` comprueba el aviso de metros ajustados (PEN-36); `e2e/map.spec.ts` comprueba que la línea punteada manual desaparece cuando ya hay resultado.
- Visual (`@visual`): capturas a 320, 390, 1024, 1440 y 1920 px de Hojas, detalle (Permisos y Actividad), Personas, Diseñadores y Revisión, con datos extremos (C-09).

## Fixtures

- `src/test/fixtures/<endpoint>.ts`: una respuesta sintética por endpoint de `contrato/CONTRATO.md`, con correos `@example.com` y nombres inventados.
- Casos obligatorios donde aplique: vacío, parcial (`incomplete` o `failed_sheets`), hoja de otra persona (`in_my_list: false`), permiso sin nombre, propio y heredado con el mismo id, cuenta dominante en actividad, regla con columna no de contacto, diseñador con `has_access: false` y `null`.

## Comandos

Desde `frontend/`: `npm run format:check`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`, `npm run test:visual`.
