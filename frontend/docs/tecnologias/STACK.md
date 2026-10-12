# Stack del frontend (planificado)

Versiones exactas en `package.json` al crear el proyecto; sin rangos (`^`, `~`). Base: el mismo stack verificado en `extractor_metadata`.

## Ejecución

- React 19 y TypeScript 5.9 estricto (`tsc --noEmit` en el build).
- Vite: servidor de desarrollo en `127.0.0.1:5710` con proxy de `/api` al backend; build a `dist/`, que FastAPI sirve en el mismo origen.
- @fluentui/react-icons: iconos de Fluent 2 importados por nombre (ADR-01).
- @tanstack/react-query: datos del servidor (ADR-02).
- react-router: rutas (ADR-04).
- CSS propio con tokens de Fluent 2; Tailwind sólo como reset si se mantiene igual que la referencia.

## Pruebas y herramientas

- Vitest + jsdom + React Testing Library + jest-dom: unitarias y de componente.
- MSW: API simulada en pruebas de componente (C-05).
- Playwright con Chromium: E2E y visual.
- ESLint con typescript-eslint, react-hooks y react-refresh. Prettier (`printWidth` 110, sin punto y coma, comillas simples).

## Restricciones

- Sin fuentes web, CDNs ni analítica.
- Sin librerías de componentes completas ni de estado global adicionales.
- Tras cambiar dependencias: `npm audit` sin vulnerabilidades y motivo registrado aquí.

## Entorno

- Node 24 (verificado en el equipo: 24.21.0).
- `VITE_API_URL` opcional; por defecto `/api` (proxy en desarrollo, mismo origen en build).
