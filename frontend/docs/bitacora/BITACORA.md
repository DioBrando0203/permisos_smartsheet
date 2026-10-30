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

## 2026-10-16 17:17 -05:00 Corrección de advertencia E2E

Estado: terminada
Cambios: configurado Playwright con directorio exclusivo `e2e/`; antes tomaba erróneamente pruebas de Vitest desde `src/` y fallaba con un error interno. Agregados los dos casos F0 explícitamente omitidos para que los comandos E2E y visual sean ejecutables sin declarar resultados de flujos que aún no existen.
Evidencia: `npm run build`, `npm run lint`, `npm test` (4 pruebas), `npm run test:e2e` (1 omitida), `npm run test:visual` (1 omitida) y `npm run format:check` pasaron a las 17:17 -05:00.
Notas: las pruebas funcionales E2E empiezan en F1 y las visuales en F6, conforme a `PLAN_CALIDAD.md`.

## 2026-10-27 16:17 -05:00 F1: shell, hojas y permisos de lectura

Estado: en curso
Cambios: aprobadas SPEC-01, SPEC-02, SPEC-03 y SPEC-05 para iniciar F1. Implementados AppLayout, rutas de los cinco destinos, banner de solo lectura, avisos globales, lista maestra de hojas con alcance, búsqueda, exportación y estados; detalle de hoja, pestañas y permisos agrupados en solo lectura. La búsqueda ignora tildes, mayúsculas y palabras de enlace; los permisos propio y heredado de una persona se agrupan sin claves duplicadas.
Evidencia: `npm run build`, `npm run lint` y `npm run format:check` pasaron; `npm test` pasó con 4 archivos y 8 pruebas; `npm run test:e2e` pasó con 1 caso F0 omitido. No se llamó a Smartsheet ni se modificaron permisos reales.
Notas: faltan los controles de escritura segura, E2E funcional y revisión visual para cerrar F1.

## 2026-10-28 10:10 -05:00 F2: directorio y detalle de personas

Estado: en curso
Cambios: aprobada SPEC-04 por solicitud explícita de continuar las vistas antes de cerrar F1. Implementados directorio con conteo de hojas, nivel más alto, filtros, búsqueda, insignias y última conexión; detalle con sus hojas, nivel y origen. Los controles de quitar acceso se muestran deshabilitados y explicados por el modo solo lectura.
Evidencia: `npm run build`, `npm run lint` y `npm run format:check` pasaron; `npm test` pasó con 5 archivos y 10 pruebas; `npm run test:e2e` pasó con 1 caso F0 omitido a las 10:10 -05:00.
Notas: no se llamó a Smartsheet ni se realizaron escrituras. F1 y F2 siguen abiertas hasta completar sus criterios de aceptación y revisión visual.

## 2026-10-28 10:28 -05:00 Corrección de arranque del frontend

Estado: terminada
Cambios: corregido el estado inicial de `App`: durante la consulta de salud ahora se muestra el indicador de conexión, en lugar de interpretar la ausencia temporal de datos como un fallo global. Formateado el archivo afectado.
Evidencia: la instancia Vite existente en `127.0.0.1:5710` respondió 200; su proxy de salud respondió 200; una comprobación de navegador confirmó el render de la lista de hojas sin errores de JavaScript. `npm run build`, `npm run lint`, `npm test` (5 archivos, 10 pruebas) y `npm run format:check` pasaron a las 10:28 -05:00.
Notas: el puerto 5710 ya estaba ocupado por esa misma instancia de Vite; no se inició un segundo servidor ni se realizaron escrituras.

## 2026-10-28 10:46 -05:00 F3: auditoría, actividad y automatizaciones por hoja

Estado: en curso
Cambios: iniciada F3 por solicitud explícita de continuar las vistas. Agregadas las pestañas Auditoría, Actividad y Automatizaciones con consultas perezosas, normalizadores por endpoint, estados de carga, vacío y error, alertas de datos desconocidos o limitaciones, estadísticas y tarjetas de automatización. El selector de período de Actividad queda en la URL.
Evidencia: `npm run build`, `npm run lint`, `npm test` (6 archivos, 12 pruebas), `npm run format:check` y `npm run test:e2e` (1 omitida) pasaron a las 10:46 -05:00. Revisión visual de Auditoría a 320, 390, 1024, 1440 y 1920 px sin desborde horizontal.
Notas: faltan Historial de fila y Calidad de datos para cerrar F3. No se realizaron escrituras; las mutaciones siguen deshabilitadas por `APP_READ_ONLY=true`.

## 2026-10-28 12:27 -05:00 CRUD base de permisos de hoja

Estado: en curso
Cambios: agregadas mutaciones pesimistas para crear, cambiar nivel y quitar permisos; la creación acepta correos pegados, descarta duplicados, permite aviso por correo y no permite Propietario. Cambiar a Administrador o bajar nivel pide confirmación; quitar también pide confirmación. `api.ts` admite correctamente el 204 de `DELETE` y las invalidaciones reutilizan `invalidateAfterShareWrite` tras confirmación del backend.
Evidencia: `npm run build`, `npm run lint`, `npm test` (7 archivos, 14 pruebas) y `npm run format:check` pasaron a las 12:27 -05:00. Las pruebas nuevas cubren 204 y destinatarios duplicados.
Notas: la UI mantiene todas las escrituras deshabilitadas con `APP_READ_ONLY=true`; no se llamó a los endpoints de escritura reales. Faltan autocompletado de contactos/grupos y E2E con Smartsheet falso para cerrar F5.

## 2026-10-28 15:35 -05:00 Autocompletado de destinatarios

Estado: terminada
Cambios: el diálogo Compartir consulta contactos y grupos sólo cuando se abre, sugiere coincidencias y permite agregar o quitar grupos antes de enviar. Se añadieron tipos, normalizadores, fixtures y handlers MSW para ambos endpoints. Los estilos del diálogo se extrajeron a `shares.css` para cumplir E-05.
Evidencia: `npm run build`, `npm run lint`, `npm test` (7 archivos, 15 pruebas), `npm run test:e2e` (1 omitida) y `npm run format:check` pasaron a las 15:35 -05:00.
Notas: no se realizaron escrituras ni consultas a Smartsheet desde las pruebas. Sigue pendiente el E2E completo contra el Smartsheet falso para cerrar F5.

## 2026-10-28 17:32 -05:00 Detalle de persona y simulación masiva

Estado: en curso
Cambios: ampliado el detalle de persona/contacto con organización, contacto, última conexión y acciones. Añadido el diálogo "Quitar de varias hojas": preselecciona sólo accesos editables, explica los bloqueados y permite pedir `dry_run=true`; el resultado muestra acciones, motivos y conteos. La ejecución real está definida en el hook pero no se ofrece activa con el modo solo lectura.
Evidencia: `npm run build`, `npm run lint`, `npm test` (8 archivos, 16 pruebas), `npm run test:e2e` (1 omitida) y `npm run format:check` pasaron a las 17:32 -05:00. Revisión visual a 320, 390, 1024, 1440 y 1920 px sin desborde horizontal.
Notas: no se ejecutó ninguna revocación real. F2 sigue abierta hasta completar las acciones por fila y el E2E especificado.

## 2026-10-30 17:16 -05:00 Especificación del mapa (PEN-29)

Estado: terminada (sólo documentación; sin código)
Cambios: nueva SPEC-11 (borrador), ADR-13 en propuesta (Leaflet 1.9.4 sin `react-leaflet`, mapa base USGS, teselas directas al proveedor como excepción a K-01), fase F7 en `PLAN_IMPLEMENTACION.md` e índice de `README.md`.
Evidencia: `npm view` el 2026-10-30: `leaflet` 1.9.4 (BSD-2-Clause, 2023-05-18), `@types/leaflet` 1.9.22 (MIT, 2026-08-01), `react-leaflet` 5.0.0 (Hippocratic-2.1, descartada). Teselas USGS en Miami: 200 en zoom 16, 404 en 17 y 18. No se ejecutaron pruebas: no hubo cambios de código.
Notas: SPEC-01 pasa a seis destinos al implementar M3; `ARQUITECTURA.md`, `STACK.md` y `CONTRATO.md` se actualizan en ese mismo cambio.
## 2026-10-30 17:41 -05:00 F7 Mapa (M3-M4)

Estado: en curso
Cambios: sexto destino `/mapa`, Leaflet diferido, modos Punto y Tramo, coordenadas, URL compartible, mapa USGS, panel de vía/jurisdicción/ubicación/parcela/fuentes y copia de fila OSP.
Evidencia: format, build, lint y 18 pruebas unitarias pasaron; Leaflet queda en chunk diferido. Audit sin vulnerabilidades con Vite 8.3.5.
Notas: faltan prueba E2E funcional y revisión visual; M5/M6 no son parte de la fase base.
