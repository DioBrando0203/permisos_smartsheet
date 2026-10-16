# Bitácora (frontend)

Una entrada por tarea, la más reciente al final. Mismo formato que `backend/docs/bitacora/BITACORA.md`.

## 2026-10-12 11:30 -05:00 Reglas, patrones UI/UX y specs iniciales

Estado: terminada
Cambios: guía, arquitectura planificada, reglas P/E/UX/C, patrones, sistema visual Fluent 2, ADR-01 a ADR-06, SPEC-01 a SPEC-04 en borrador.
Evidencia: sólo documentación; sin código ni pruebas.
Notas: la implementación espera al backend (PEN-06).

## 2026-10-16 -05:00 Documentación del frontend lista para empezar

Estado: terminada
Cambios: alineada con el backend implementado (28 endpoints). Nuevos: `contrato/CONTRATO.md` (endpoint, hook, caché, invalidación, textos de error), `PLAN_IMPLEMENTACION.md` (F0 a F6), SPEC-05 a SPEC-09 (detalle de hoja con pestañas, revisión, comparar y copiar, diseñadores, calidad y referencias), ADR-07 a ADR-12 (puertos y proxy, modo solo lectura, gráficos con CSS, pruebas sin la cuenta real, pestañas, filtrado en el navegador), UX-28 a UX-35, P-32 a P-36, C-15 a C-17, bloqueos FB-01 a FB-06. Reescritas: ARQUITECTURA (cinco destinos y once features), STACK (versiones exactas y `vite.config.ts`), PLAN_CALIDAD, SPEC-01 a SPEC-04 (forma real del contrato). Actualizados: README, GUIA_IA, patrones, sistema visual; AGENTS y PEN-06 del backend.
Evidencia: versiones verificadas con `npm view` (react-query 5.104.0 del 2026-09-26, react-router 8.4.0 del 2026-09-15, msw 3.0.1 del 2026-09-30); configuraciones tomadas de `extractor_metadata/frontend`. Sin código ni pruebas aún.
Notas: decisión de puertos (ADR-07): desarrollo en 5710 estricto porque el `Origin` de la página debe estar permitido y no se reescribe en el proxy; uso diario con el build servido por el backend en su puerto (8710 o al azar).

## 2026-10-16 16:38 -05:00 F0-F1 a F0-F5: base del frontend

Estado: terminada
Cambios: creado el proyecto Vite React TypeScript con versiones exactas del STACK; configuración de Vite, TypeScript, ESLint y Prettier de la referencia; tokens Fluent recortados y estilos base; componentes UI reutilizables; fachada HTTP con `ApiError` (K-03 a K-05), normalizadores, tablas de niveles, errores y severidad, utilidades y caché de TanStack Query; pantalla de arranque con cuenta y banner de modo solo lectura; MSW con fixture sintético y handler de salud.
Evidencia: `npm run build`, `npm run lint`, `npm test` (1 archivo, 1 prueba) y `npm run format:check` pasaron a las 16:38 -05:00. `npm audit --omit=dev` y `npm audit`: 0 vulnerabilidades.
Notas: F0 no incluye rutas ni vistas de negocio; el siguiente trabajo es F1.

## 2026-10-16 16:56 -05:00 Revisión de detalles F0 y conexión de desarrollo

Estado: terminada
Cambios: agregado `frontend/.env` local con su plantilla `.env.example` y carga explícita de variables en Vite; vacío sigue automáticamente el puerto de `backend/.port` y permite forzar un backend con `VITE_BACKEND_URL`. Mejorada la base UI: diálogo con id accesible, foco inicial en Cancelar y devolución de foco; búsqueda limpia con Esc; los errores iniciales usan su código `ApiError`; las invalidaciones usan exclusivamente `queryKeys`. Los tipos crudos de salud y cuenta se centralizaron en `lib/types.ts` y se ampliaron las pruebas MSW para K-03, K-04 y K-05.
Evidencia: `npm run build` pasó con `.env` y con `VITE_BACKEND_URL=http://127.0.0.1:8710`; `npm run lint`, `npm test` (4 pruebas) y `npm run format:check` pasaron a las 16:56 -05:00. `npm audit --omit=dev` y `npm audit`: 0 vulnerabilidades.
Notas: no se adelantó F1 ni se llamó a Smartsheet.
