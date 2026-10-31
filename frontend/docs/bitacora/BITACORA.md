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

## 2026-10-30 19:27 -05:00 F7: E2E del mapa, marcador y docs del buscador

Estado: terminada (fase base de F7)
Cambios: `node_modules` desde el lock y Chromium de Playwright en el equipo Windows nuevo. `playwright.config.ts` con `webServer` (Smartsheet falso 8791, GIS falso 8792, backend de prueba 8793, Vite 5791; nunca reutiliza servidores) y `e2e/map.spec.ts` (tramo de control por URL, clics fuera y sobre la vía, buscador, 320 px). Corregida la carrera de `MapView` que perdía el marcador (FB-07). Docs: SPEC-11 (buscador, botones de copiar por campo, CA-10 y CA-11, estado real de cada CA), `CONTRATO.md` (`useMapSearch`), `ARQUITECTURA.md`, `PLAN_CALIDAD.md` y F7 en `PLAN_IMPLEMENTACION.md`.
Evidencia: format, build, lint, 22 pruebas unitarias y 4 E2E pasaron; E2E repetido 4 veces sin fallos; revisión visual a 320, 1024 y 1440 px (detalle en RESULTADOS).
Notas: pendientes del mapa en SPEC-11: encuadrar el tramo completo al abrirlo por URL, pruebas de CA-04 y del aviso "Datos parciales", M5 y el resto de M6. No se llamó a Smartsheet ni a GIS reales.

## 2026-10-30 20:28 -05:00 PEN-31 vista del mapa y PEN-30 en el panel

Estado: terminada
Cambios: `components/map/tileSources.ts` (USGS, "Satélite HD" con NAIP y capa de vías del FDOT por área con `{bbox}`), `MapView` con capa opcional, escala y zoom 20; `MapToolbar` sale de `MapPage`; preferencias en `lib/preferences.ts`; nombres de fuentes en `lib/sources.ts`; Ubicación con Estado y Parcela con su fuente; `parcel.source` en tipos, normalización y fixture; tokens `--map-road-state` y `--map-road-county`. Docs: SPEC-11 (CA-12 y CA-13), ampliación de ADR-13, `ARQUITECTURA.md` y `CONTRATO.md`.
Evidencia: format, build, lint, 23 pruebas unitarias y 5 E2E; captura manual con servicios reales (detalle en RESULTADOS).
Notas: la NAIP es más lenta (unos 8 s por vista a zoom 19), por eso es opción y no el mapa por defecto. La línea del FDOT puede quedar a unos metros de la calle de la foto.

## 2026-10-30 21:11 -05:00 PEN-32 modo Trazo y PEN-33 límites de parcelas

Estado: terminada
Cambios: el modo Tramo pasa a Trazo como en OSP (useTraceDrawing, TraceResult, WorkLocationTable; clic por vértice, doble clic, Enter o Terminar; Deshacer y Borrar; URL ?t= y enlaces viejos ?a=&b=); tabla con las columnas de OSP, copiar fila y tabla. Casilla "Límites de parcelas" (useParcelLayer, lib/cells.ts, celdas con useQueries y combine). MapView con lines, outlines, drawing, onMapDoubleClick y onViewChange; dibujos sin clic propio. Se quitaron useMapSegment, SegmentResult y OspSection. Docs: SPEC-11 (puntos 5, 7 a 10, CA-02, CA-05, CA-14 y CA-15), CONTRATO.md, ARQUITECTURA.md, PLAN_IMPLEMENTACION.md, FB-08 y FB-09.
Evidencia: format, build, lint, 27 pruebas unitarias y 7 E2E; capturas con servicios reales (detalle en RESULTADOS).
Notas: sin commit todavía; pendiente encuadrar el trazo completo al abrirlo por URL y un "Actualizar" que pida refresh=true.

## 2026-10-31 10:18 -05:00 Zona y cruce en el buscador del mapa (PEN-34)

Estado: terminada
Cambios: `MapScopePicker` (Condado con los cuatro del equipo primero y Ciudad con los municipios del condado), `area.ts` (zona y su normalización), `useMapCounties`, `useMapArea` y `useMapSearch` con zona; campo "Cruce con (opcional)"; sugerencias "Cruce" con milepost y "Punto más cercano"; `MapView` encuadra un rectángulo y dibuja el límite punteado de la zona; el panel pone primero la vía del resultado elegido; espera del buscador de 350 a 500 ms; `MAP_AREA_NOT_FOUND` en `errorMessages`.
Evidencia: format, lint, build, 31 pruebas unitarias y 8 E2E (1 omitido de antes) a las 10:14. Recorrido con Playwright sobre el servidor de desarrollo y datos reales: Broward, Fort Lauderdale, "Las Olas" y "3rd Ave" dan "E LAS OLAS BLVD y SE 3 AVE · Cruce · MP 0.258"; al elegirlo, el marcador cae en el cruce y el panel muestra la vía `86000142` en 0.258. Capturas fuera del repositorio.
Notas: SPEC-11 CA-16 y CA-17, CONTRATO y ARQUITECTURA actualizados. Mientras el Censo bloquee la IP (B-15 del backend) sólo responden las fuentes del FDOT. Sin commit.

## 2026-10-31 10:58 -05:00 Resultado de trazo ajustado a FDOT (PEN-35)

Estado: terminada
Cambios: al responder el trazo se oculta la línea manual y se dibujan sólo sus LineString LRS; se informa la longitud oficial y, cuando difiere, la marcada. Una URL de trazo encuadra todas las filas oficiales. Nuevos tipos y normalización para `input_length_mi`, prueba pura y comprobación E2E de que desaparece el borrador.
Evidencia: build, lint, formato, 32 pruebas unitarias y 8 E2E funcionales aprobados; ver `calidad/RESULTADOS.md`.
Notas: no es enrutamiento: sigue siendo necesario corregir un trazo que no siga la vía o esté a más de 25 m.
Entrega: commit local `d091361` creado. El `git push` del 2026-10-31 10:59 -05:00 no llegó a GitHub porque el entorno no dispone de credenciales; queda pendiente de una sesión autenticada.

## 2026-10-31 11:30 -05:00 Revisión de trazos incompletos y Actualizar (PEN-37)

Estado: terminada
Cambios: `TraceQuality` muestra cobertura y huecos, `useMapDrawing` conserva/encuadra referencia punteada si falta geometría o recorrido. Longitudes desconocidas conservan `null`. `useMapReading` implementa Actualizar con `refresh=true` para punto/trazo y errores visibles aunque haya caché anterior. Se cuenta cada vía una vez aunque tenga varias filas separadas. Etiqueta de extremos corregida: el panel calcula distancias con datos FDOT. Specs, contrato y arquitectura actualizados (P-07, P-09, UX-19, UX-20, UX-31).
Evidencia: build/lint/formato limpios, 37 unitarias, 9 E2E funcionales y 1 omitida; capturas en cinco anchos sin desborde y revisión visual de 390/1440 px. RESULTADOS detalla la ejecución secuencial por recursos de la VM (FB-10).
Pendiente de producto: comparación independiente de OSP con idénticos vértices, adaptadores M5 y respaldos Palm Beach/Martin (PEN-29). Sin escrituras en Smartsheet.
Entrega: commit local `a02cd17`; `git push` falló por falta de credenciales HTTPS en esta sesión (`could not read Username`). Pendiente subir desde una sesión autenticada.

## 2026-10-31 12:40 -05:00 Verificación del ajuste automático en el mapa (PEN-38)

Estado: terminada
Cambios: sin cambios de código; el frontend de PEN-38 (`TraceOptions`, `TraceAlignmentNote`, URL `snap`/`original`) llegó en el commit `d2c9999`. Plan de implementación y RESULTADOS actualizados.
Evidencia: build, lint, formato, 39 unitarias y 11 E2E (1 omitida de F0). Revisión con Playwright contra el GIS real a 1440 y 320 px: dos líneas en la diagonal de Miami, Broward Blvd ajustado al eje, comparación con el dibujo original y sin desborde.
Pendiente de producto: comparación con OSP usando idénticos vértices (OSP-PEN-01), adaptadores M5 y respaldos de parcelas Palm Beach/Martin (PEN-29). Sin escrituras en Smartsheet.
