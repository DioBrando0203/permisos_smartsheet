# Plan de calidad (frontend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`. Aún no hay código (F0 pendiente).

## Capas de prueba

- Unitarias (Vitest, sin DOM): `lib/search`, `lib/accessLevels`, `lib/severity`, `lib/errorMessages`, `lib/normalize` (una por endpoint, C-17), `lib/routes`, `lib/formatters`, `features/shares/lib/groupShares` (propio + heredado con el mismo id, B-05), `features/shares/lib/recipients`, extractor de código de permalink (SPEC-07), armado de la query de calidad (SPEC-09), filtros rápidos de personas (SPEC-04).
- Componente (React Testing Library + MSW): una prueba por CA marcado "componente" en SPEC-01 a SPEC-09; cada vista con escrituras en `read_only: true` y `false` (C-15); cada consulta larga con demora y con `failed_sheets` (C-16).
- E2E (Playwright, ADR-10): configuración separada en `playwright.config.ts`, con pruebas en `e2e/` para no mezclar Vitest y Playwright. F0 sólo declara los casos pendientes; la primera prueba funcional llega con F1. Después: `webServer` con el Smartsheet falso, el backend apuntando a él (`SMARTSHEET_BASE_URL`, `APP_READ_ONLY=false` sólo en ese proceso) y `npm run dev`. Flujos: navegar hojas → detalle → pestañas; persona por URL con `@`; comparar por URL; dar, cambiar y quitar (F5) verificando las escrituras que registró el Smartsheet falso.
- Visual (`@visual`): capturas a 320, 390, 1024, 1440 y 1920 px de Hojas, detalle (Permisos y Actividad), Personas, Diseñadores y Revisión, con datos extremos (C-09).

## Fixtures

- `src/test/fixtures/<endpoint>.ts`: una respuesta sintética por endpoint de `contrato/CONTRATO.md`, con correos `@example.com` y nombres inventados.
- Casos obligatorios donde aplique: vacío, parcial (`incomplete` o `failed_sheets`), hoja de otra persona (`in_my_list: false`), permiso sin nombre, propio y heredado con el mismo id, cuenta dominante en actividad, regla con columna no de contacto, diseñador con `has_access: false` y `null`.

## Comandos

Desde `frontend/`: `npm run format:check`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`, `npm run test:visual`.
