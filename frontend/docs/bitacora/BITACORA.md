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
