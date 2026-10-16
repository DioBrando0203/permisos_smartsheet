# Stack del frontend

Versiones exactas, sin `^` ni `~` (P-31). Base: las versiones verificadas en `extractor_metadata` (2026-10); las tres dependencias nuevas, con al menos dos semanas de publicadas al 2026-10-16. Al instalar, revisar en la documentación de cada una que la API usada coincide con la versión (React Router 8 y MSW 3 son mayores recientes).

## Ejecución

- react 19.3.0, react-dom 19.3.0.
- typescript 5.9.3 estricto; `tsc --noEmit` dentro de `npm run build`. TypeScript 7 existe pero no está verificado en la referencia.
- vite 8.3.2 con @vitejs/plugin-react 5.2.0.
- @tailwindcss/vite 4.3.3 y tailwindcss 4.3.3: sólo el reset (preflight) y el empaquetado de `@import`, como en la referencia; sin utilidades en JSX (P-30).
- @fluentui/react-icons 2.0.343: iconos importados por nombre (ADR-01).
- @tanstack/react-query 5.104.0 (2026-09-26): datos del servidor (ADR-02).
- react-router 8.4.0 (2026-09-15): rutas (ADR-04).

## Pruebas y herramientas

- vitest 5.0.3 + jsdom 30.1.2 + @testing-library/react 16.3.3 + @testing-library/user-event 14.6.7 + @testing-library/jest-dom 7.0.1.
- msw 3.0.1 (2026-09-30): API simulada en pruebas de componente (ADR-10).
- @playwright/test 1.63.0 con Chromium (`npx playwright install chromium`).
- eslint 10.12.0, @eslint/js 10.0.1, typescript-eslint 8.71.1, eslint-plugin-react-hooks 7.1.1, eslint-plugin-react-refresh 0.5.7, globals 17.13.0.
- prettier 3.9.9.
- @types/react 19.3.0, @types/react-dom 19.3.0.

## Scripts de `package.json`

- `dev`: `vite`.
- `build`: `tsc --noEmit && vite build`.
- `lint`: `eslint .`.
- `test`: `vitest run`; `test:watch`: `vitest`.
- `test:e2e`: `playwright test --grep-invert @visual`; `test:visual`: `playwright test --grep @visual`.
- `format`: `prettier --write .`; `format:check`: `prettier --check .`.

## Configuración

- `tsconfig.json`, `eslint.config.js`, `prettier.config.js` y `src/test/setup.ts`: iguales a `extractor_metadata/frontend` (copiar y ajustar el nombre del proyecto).
- `vite.config.ts` (ADR-07):

```ts
import { readFileSync } from 'node:fs'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Dirección del backend: VITE_BACKEND_URL, si no el puerto que escribió run.py, si no 8710.
function backendUrl(): string {
  if (process.env.VITE_BACKEND_URL) return process.env.VITE_BACKEND_URL
  try {
    const port = readFileSync('../backend/.port', 'utf8').trim()
    if (/^\d+$/.test(port)) return `http://127.0.0.1:${port}`
  } catch {
    // Sin archivo: el backend no se inició con run.py o usa el puerto por defecto.
  }
  return 'http://127.0.0.1:8710'
}

const target = backendUrl()

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // strictPort: 5710 es el único origen de desarrollo que el backend acepta para escribir.
  server: {
    host: '127.0.0.1',
    port: 5710,
    strictPort: true,
    proxy: { '/api': { target }, '/docs': { target }, '/openapi.json': { target } },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
  },
})
```

- El proxy no reescribe `Origin` (ADR-07): el backend sigue viendo `http://127.0.0.1:5710`, que está en `APP_ALLOWED_ORIGINS`.

## Restricciones

- Sin fuentes web, CDNs ni analítica.
- Sin librerías de componentes completas (ni `@fluentui/react-components`), de estado global ni de gráficos (ADR-01, ADR-09).
- Tras cambiar dependencias: `npm audit --omit=dev` y `npm audit` sin vulnerabilidades, y el motivo aquí.

## Entorno

- Node 24 (verificado en el equipo: 24.21.0, npm 11.19.0).
- `frontend/.env`: copia local de `.env.example`, contiene `VITE_BACKEND_URL`. Vacío: Vite lee `backend/.port` y, si aún no existe, usa `http://127.0.0.1:8710`; es el modo local normal y sigue el puerto aleatorio de `run.py`.
- Para forzar otro backend de desarrollo, asignar una URL en `VITE_BACKEND_URL`. Nunca poner tokens, correos ni otros datos privados: toda variable `VITE_*` es visible para el navegador.
