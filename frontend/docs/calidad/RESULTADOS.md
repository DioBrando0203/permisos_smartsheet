# Resultados verificados (frontend)

Sólo ejecuciones reales, con fecha America/Lima (C-13).

## 2026-10-16 16:38 -05:00 F0

- `npm run build`: pasa. TypeScript estricto y Vite completaron el build de producción.
- `npm run lint`: pasa, sin errores ni warnings.
- `npm test`: pasa. 1 archivo y 1 prueba: cliente HTTP y normalización de `/api/health` con MSW.
- `npm run format:check`: pasa.
- `npm audit --omit=dev` y `npm audit`: pasan, 0 vulnerabilidades.

## 2026-10-16 16:56 -05:00 Revisión F0

- `npm run build`: pasa con la resolución automática de `frontend/.env` y con `VITE_BACKEND_URL=http://127.0.0.1:8710`.
- `npm run lint`: pasa, sin errores ni warnings.
- `npm test`: pasa. 1 archivo y 4 pruebas: éxito, error de backend, 422 y backend inaccesible con MSW.
- `npm run format:check`: pasa.
- `npm audit --omit=dev` y `npm audit`: pasan, 0 vulnerabilidades.

## 2026-10-16 17:17 -05:00 Corrección de runners de prueba

- `npm run build`, `npm run lint`, `npm test` (4 pruebas) y `npm run format:check`: pasan.
- `npm run test:e2e`: pasa. 1 caso marcado omitido: F1 define el primer flujo funcional.
- `npm run test:visual`: pasa. 1 caso marcado omitido: F6 define las primeras capturas.
