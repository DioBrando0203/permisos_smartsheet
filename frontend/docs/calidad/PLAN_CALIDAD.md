# Plan de calidad (frontend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`.

## Capas de prueba (planificado)

- Unitarias (Vitest): `lib/search`, `lib/accessLevels`, `lib/errorMessages`, `lib/normalize`, `features/shares/lib/recipients`, `features/shares/lib/groupShares`.
- Componente (React Testing Library + MSW): `ShareTable`, `ShareDialog`, `RemoveShareDialog`, `AccessLevelSelect`, `SheetList`, `PeopleList`; por rol y nombre accesible.
- E2E (Playwright): backend real con Smartsheet simulado; flujos de SPEC-01 a SPEC-04.
- Visual (Playwright `@visual`): capturas a 320, 390, 1024, 1440 y 1920 px con datos extremos (C-09).

## Comandos

Desde `frontend/`: `npm run format:check`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`, `npm run test:visual`.
