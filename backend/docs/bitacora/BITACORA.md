# Bitácora (backend)

Una entrada por tarea, la más reciente al final. Formato fijo:

```text
## AAAA-MM-DD HH:MM -05:00 Título corto
Estado: terminada | parcial | bloqueada
Cambios: qué se tocó
Evidencia: comandos ejecutados y resultado real
Notas: decisiones, ADR o bloqueos relacionados
```

No se registran nombres ni correos de personas reales.

## 2026-10-12 11:30 -05:00 Documentación inicial y configuración del token

Estado: terminada
Cambios: `backend/.env` con `SMARTSHEET_ACCESS_TOKEN`, `.env.example`, `.gitignore`; README, AGENTS; docs de backend (guía, arquitectura, requerimientos, SPEC-B01 a B04, ADR-B01 a B09, reglas PY/SM/ES/QB, patrones, API, stack, calidad, bloqueos) y de frontend (guía, arquitectura planificada, specs en borrador, reglas P/E/UX/C, patrones UI/UX, sistema visual).
Evidencia: lecturas reales con curl contra la API 2.0 (ver `calidad/RESULTADOS.md`); ninguna escritura.
Notas: estructura y metodología tomadas de `extractor_metadata` (SDD, docs para IA con IDs citables). Escrituras de `/shares` pendientes de verificar (B-01, PEN-07).

## 2026-10-12 12:40 -05:00 Backend: CRUD de permisos, directorio con contactos y modo solo lectura

Estado: terminada (escrituras reales pendientes de PEN-07 por decisión del usuario)
Cambios: `pyproject.toml`, `requirements.lock`, `app/` completo (config, errores, Origin, cliente Smartsheet con reintentos y paginación, reglas de permisos, caché, servicios de hojas, permisos y directorio, rutas), `tests/` con respx. Puertos 8710 y 5710 (pedido del usuario). `APP_READ_ONLY=true` en `.env`. Docs: ADR-B10 (directorio), ADR-B11 (solo lectura), specs B01 a B04 implementadas, API, arquitectura, requerimientos.
Evidencia: ver `calidad/RESULTADOS.md` (53 pruebas, ruff, lecturas reales, escrituras bloqueadas).
Notas: `/contacts` no es la lista de gente con acceso: es la libreta del dueño del token (ADR-B10). El usuario no quiere crear ni cambiar nada por ahora; probará crear un usuario después (PEN-13).

## 2026-10-12 13:10 -05:00 Hoja por código de permalink y ejemplo en Swagger

Estado: terminada
Cambios: `{sheet_id}` acepta el id numérico o el código del permalink (`SheetService.resolve_id`, dependencia `SheetId` en `api/deps.py`); ejemplos de Swagger con una hoja real (SPEC-B01 7 y 8, CA-07; API.md).
Evidencia: 54 pruebas aprobadas; ruff limpio. Contra la cuenta real, el permalink `QMFVM7v3…` y el id `1842596423880580` devuelven la misma hoja con 30 permisos (28 editables).
Notas: el usuario intentó usar el código del permalink como id; ahora funciona.

## 2026-10-12 14:10 -05:00 Auditoría, comparación, resumen de acceso y operaciones masivas

Estado: terminada (ejecución real de operaciones masivas pendiente de PEN-07)
Cambios: SPEC-B05 y SPEC-B06; ADR-B12 y ADR-B13; `services/audit_rules.py`, `reports.py`, `bulk_plans.py`, `bulk.py`; `models/reports.py`, `bulk.py`; rutas `reports.py` y `bulk.py`; `PeopleService` expone contactos, organización y permisos por hoja con caché; `ShareService.ensure_writable` público. Ejemplos de Swagger: planes Crown Castle 2026 y 2025 (pedido del usuario).
Evidencia: `calidad/RESULTADOS.md` (71 pruebas, lecturas y simulaciones reales).
Notas: los planes antiguos se siguen modificando, por eso el resumen no infiere inactividad sólo por fecha.

## 2026-10-12 14:45 -05:00 Marca de Dynamic View y revisión de riesgos de la cuenta

Estado: terminada
Cambios: `APP_DYNAMIC_VIEW_SHEETS` y `has_dynamic_view` (PEN-17, B-07); SPEC-B07 con `GET /api/review` (`services/account_review.py`); `audit_rules.build_facts` compartido con la auditoría por hoja; PEN-18 a PEN-20 nuevos; trazabilidad y OAuth anotados en PEN-08.
Evidencia: `calidad/RESULTADOS.md` (75 pruebas; revisión real de 100 hojas).
Notas: el usuario preguntó por replicar Dynamic View en el servicio; se desaconsejó (trazabilidad a nombre del token, seguridad, términos de Smartsheet, límite de 300 por minuto) y se propusieron mejoras de gobierno de permisos.

## 2026-10-16 -05:00 Arranque sin escribir el puerto

Estado: terminada
Cambios: `iniciar.py`, `backend/app/launcher.py`, `APP_PORT` en `Settings` (orígenes del puerto real), `tests/test_launcher.py`; README (sección Arranque), AGENTS, RQ-15, ADR-B14, arquitectura.
Evidencia: `calidad/RESULTADOS.md`.
Notas: pedido del usuario: un solo puerto y, si no está libre, uno al azar.

## 2026-10-16 -05:00 Arranque con `python run.py`

Estado: terminada
Cambios: `backend/run.py` (mismo lanzador); README y AGENTS.
Evidencia: con el entorno activado, `python run.py` arrancó en 8710 y `/api/health` respondió; instancia de prueba detenida.
Notas: el usuario quiere `cd`, activar el entorno y un solo comando sin argumentos.

## 2026-10-16 -05:00 Un solo modo de arranque

Estado: terminada
Cambios: se quitó `iniciar.py` de la raíz por pedido del usuario; el arranque es sólo desde `backend` con `python run.py`. README, AGENTS, ADR-B14, RQ-15, arquitectura y docstrings actualizados. Las entradas anteriores de bitácora y resultados que mencionan `iniciar.py` se conservan como historial.

## 2026-10-16 -05:00 Guía de levantamiento y fuentes de actividad

Estado: terminada
Cambios: `LEVANTAMIENTO.md` (Windows y Linux) enlazado desde README; B-08 y PEN-21; resultados de las pruebas de actividad.
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario preguntó por logs de quién modifica qué; no existe endpoint propio (PEN-09 pendiente) y Event Reporting no está en el plan.

## 2026-10-16 -05:00 Actividad de una hoja, directo de Smartsheet

Estado: terminada (backend)
Cambios: SPEC-B08; `client.list_columns`, `list_rows_with_authors`, `get_row_filled_columns`, `get_cell_history`; `services/activity_rules.py`, `activity.py`; `models/activity.py`; `routes/activity.py`; aviso de cuenta dominante.
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario creía que el registro de actividad de la web tenía API; se verificó que no (404) y que Event Reporting no está en el plan (403).

## 2026-10-16 -05:00 Event Reporting y plan Enterprise

Estado: terminada
Cambios: B-08 precisado (complemento de pago aun en Enterprise); PEN-22.
Evidencia: `/events` 403 1013 con tres variantes de parámetros; documentación y comunidad de Smartsheet.
Notas: el usuario preguntó si siendo Enterprise sí tendría el registro.

## 2026-10-16 -05:00 Webhooks, includeAll retirado y propuesta de servicios propios

Estado: terminada (investigación)
Cambios: B-09, PEN-23, PEN-24; resultados de webhooks.
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario preguntó si podemos cubrir lo que Smartsheet hace mal sin Jira ni Salesforce.

## 2026-10-16 -05:00 Organización, última conexión, calidad de datos y exportación

Estado: terminada
Cambios: PEN-14 (`/users/sheets`, `in_my_list`, `owner_email`, `scope`, `NOT_SHARED_WITH_TOKEN`); PEN-15 (`last_login`); SPEC-B09 (`columns`, `quality`, `quality_rules`); PEN-12 (`export/access.csv`); lectura de filas generalizada (`client.list_rows`) y columnas con caché en `SheetService`; BOM con nombre explícito.
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario pidió continuar con endpoints y servicios que mejoren lo que falta (ADR-B15).

## 2026-10-16 -05:00 Salud de las automatizaciones (PEN-25)

Estado: terminada
Cambios: SPEC-B10; `client.list_automation_rules`, `RawAutomation`, `mappers.to_automation`; `services/automation_rules.py`, `automations.py`; `models/automations.py`; `routes/automations.py`; `client.py` dividido en `client.py` y `transport.py` (PY-01).
Evidencia: `calidad/RESULTADOS.md`.
Notas: se corrigió la hipótesis previa (no fallan por `Designer1`: ninguna regla la usa). Se le dijo al usuario.

## 2026-10-16 -05:00 Referencias entre hojas y logs de httpx

Estado: terminada
Cambios: SPEC-B11 (`services/references.py`, `routes/references.py`, `quality_rules.normalized_values` y `missing_references`; `QualityService.rows`, `find_column` y `limit_issues` públicos); B-10 (httpx en WARNING).
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario aprobó seguir con la validación entre hojas; no hay hoja maestra de Record IDs, se usó el catálogo de diseñadores. Nombres reales sólo se mostraron al usuario en la conversación, no en docs.

## 2026-10-16 -05:00 Carga y acceso de diseñadores (SPEC-B12)

Estado: terminada
Cambios: SPEC-B12; `services/workload_rules.py`, `designers.py`; `models/designers.py`; `routes/designers.py`; configuración `APP_DESIGNER_*`, `APP_STATUS_COLUMN`, `APP_CLOSED_STATUSES` (en `.env` y `.env.example`); `ReferenceService.catalog` público; PEN-27.
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario pidió un servicio que Smartsheet no tenga y que combine los endpoints existentes (ADR-B15).

## 2026-10-16 -05:00 F0 del backend: build del panel, `.port`, Smartsheet falso y Swagger

Estado: terminada
Cambios: `app/frontend.py` y `create_app(frontend_dist=...)` (F0-B1); `.port` en `launcher` con cierre ordenado y SIGTERM, `.gitignore` (F0-B2, B-11); `tests/fake_data.py`, `tests/fake_smartsheet.py`, `test_fake_smartsheet.py` (F0-B3); `routes/review.py` con un solo grupo y prueba de grupos únicos (F0-B4).
Evidencia: `calidad/RESULTADOS.md`.
Notas: el usuario pidió "arreglarlo" y qué es el Smartsheet falso; se explicó y se implementó.

## 2026-10-29 17:01 -05:00 Servidores de prueba con escrituras habilitadas

Estado: en curso
Cambios: por instrucción explícita del usuario, `backend/.env` usa `APP_READ_ONLY=false`; se inició backend en 8710 y frontend Vite en 5710.
Evidencia: `GET /api/health` directo y mediante el proxy del frontend devolvieron 200 con `read_only:false` a las 17:01 -05:00.
Notas: no se ejecutó ninguna escritura. La prueba manual de POST, PATCH o DELETE sigue requiriendo una hoja y un correo de prueba designados por el usuario (PEN-07).

## 2026-10-30 17:16 -05:00 Especificación del mapa (PEN-29)

Estado: terminada (sólo documentación; PEN-29 sigue sin código)
Cambios: nuevos RQ-26, PEN-29 con fases M1 a M6, SPEC-B14 (borrador), ADR-B16 (módulo del mismo backend, en Python) y ADR-B17 (fuentes GIS públicas y datos de propietarios), ambos en propuesta; índice de `README.md` actualizado.
Evidencia: consultas GET reales sin sesión a FDOT y FDACS el 2026-10-30, que reproducen el caso de control de OSP (vía 87281000, sección 281, milepost 3.124 a 3.839), detalladas en `future_docs/GIS_PUBLICO_FLORIDA.md` y `future_docs/MAPAS_JURISDICCION_PARCELAS.md`. No se ejecutaron pruebas automáticas: no hubo cambios de código.
Notas: ADR-B16 y ADR-B17 requieren aprobación del usuario antes de M1. Sin dependencias nuevas previstas en el backend.
## 2026-10-30 17:41 -05:00 Mapa GIS base (PEN-29, M1-M2)

Estado: en curso
Cambios: aprobadas ADR-B16 y ADR-B17; implementados transporte GIS sin token, reglas puras, caché de una hora, `GET /api/map/point`, `/segment` y `/sources`, contrato y pruebas simuladas.
Evidencia: 137 pruebas, ruff limpio y GET manual del tramo de control: SR 953, `87281000`, sección `281`, mileposts 3.124 a 3.839; las ocho fuentes respondieron `ok`.
Notas: no hubo escrituras en Smartsheet. Quedan M5/M6 y el E2E del mapa.

## 2026-10-30 19:27 -05:00 Entorno en Windows y GIS falso para E2E (PEN-29)

Estado: terminada
Cambios: entorno aislado en un equipo Windows nuevo (`backend/.venv` con Python 3.14.7; nada global). Nuevos `tests/fake_gis.py` y `tests/fake_gis_data.py` (GIS falso con la vía sintética del caso de control), `tests/e2e_backend.py` (backend para el E2E del frontend, solo lectura, sin leer token ni URL de `.env`) y sus pruebas. Docs del buscador agregado en el commit "mapa mejorado": SPEC-B14 (punto 9, contrato `MapSearch`, CA-12 y CA-13, fuente del Censo), `estilos/API.md`, `ARQUITECTURA.md`, PEN-29 y `PLAN_CALIDAD.md`. Nuevo B-12 (Python 3.11 a 3.13) con el requisito corregido en `LEVANTAMIENTO.md`, `README.md` y `STACK.md`.
Evidencia: `pytest` 156 aprobadas; `ruff check` y `ruff format --check` sin observaciones (detalle en RESULTADOS).
Notas: el geocodificador del Censo es una fuente nueva que ADR-B17 no nombraba; queda pendiente confirmarla con el usuario y verificar el buscador con GET reales. B-12 queda abierto hasta decidir entre corregir las anotaciones o exigir 3.14. No hubo escrituras en Smartsheet.

## 2026-10-30 20:28 -05:00 PEN-30: fuente caída y parcela de respaldo

Estado: terminada para Broward
Cambios: `transport.py` con plazo de conexión de 5 s, sin reintentos si no conecta y pausa de 120 s para ese host; respaldo de parcelas de Broward en `MapService` (`broward_parcels`, sólo folio) y `Parcel.source`; ajustes nuevos en `config.py`; fuente en `/api/map/sources`; GIS falso y backend del E2E apuntados también al respaldo. Docs: PEN-30 y PEN-31 en REQUERIMIENTOS, SPEC-B14 (CA-14 y CA-15), `API.md`, ampliación de ADR-B17, B-13 (FDACS sin conexión) y B-14 (recarga de Uvicorn en Windows), `PLAN_CALIDAD.md`.
Evidencia: 160 pruebas y ruff limpio; manual: de 60,8 s a 6,0 s y 1,6 s con folio (detalle en RESULTADOS).
Notas: otros condados siguen sin respaldo; condiciones de uso de la capa de Broward por revisar (MJ-PEN-06). Los puntos consultados mientras FDACS falla quedan en caché una hora sin uso ni propietario. Sólo `refresh=true` los vuelve a pedir: el panel no lo ofrece todavía ("Reintentar" sólo aparece ante un error y no salta la caché del backend); anotado en PEN-30.

## 2026-10-30 21:11 -05:00 PEN-32 trazo y PEN-33 contornos de parcelas

Estado: terminada
Cambios: commit 9cc3e8f subido a main a pedido del usuario. Nuevos trace_rules.py (puro), map_trace.py, map_parcels.py y gis/timing.py (medición compartida con el buscador); GisClient.query_box; GET /api/map/trace y /api/map/parcels; modelos WorkLocation, MapTrace y ParcelOutlines; osp_row.state_road_id del tramo pasa a ser la ruta (SR 953), como OSP; Turnpike con la capa 13 (D8). GIS falso con rectángulos, distritos y parcelas de Miami-Dade. Docs: PEN-32 y PEN-33, SPEC-B14 (puntos 10 y 11, CA-16 a CA-19), API.md, ARQUITECTURA.md, ampliación de ADR-B17, PLAN_CALIDAD.md y GIS-PEN-01 en future_docs.
Evidencia: 176 pruebas y ruff limpio; GET reales del trazo y de los contornos (detalle en RESULTADOS).
Notas: falta comparar el Turnpike con OSP en un tramo del Turnpike; Palm Beach y Martin sin contornos propios (usan FDACS, inaccesible desde este equipo, B-13).

## 2026-10-31 10:18 -05:00 Ubicarse por condado, ciudad, calle y cruce (PEN-34)

Estado: terminada
Cambios: `GET /api/map/counties`, `GET /api/map/area` y `county`/`city` en `/api/map/search`; cruces "A & B" desde el FDOT (capa 6 de RCI, con milepost del cruce), el geocodificador del Censo y un cálculo con calles TIGER; calles locales del Censo dentro de la zona; filtros por inicio de palabra (`word_like`). Nuevos `map_places.py`, `map_streets.py` y `map_geometry.py` (puro); `GisClient.query_where` con rectángulo y simplificación; `gis_tiger_roads_url`. El transporte trata una respuesta que no es JSON como fuente caída y salta ese host (B-15). GIS falso con condado, ciudades, cruces y TIGER; E2E apuntado al TIGER falso.
Evidencia: 188 pruebas, `ruff check` y `ruff format --check` limpios a las 10:16. GET reales el 2026-10-31: 67 condados; Broward con 31 municipios; Fort Lauderdale con su contorno; Las Olas y 3rd Ave en MP 0.258 de `86000142`; Broward Blvd y Andrews Ave en MP 6.773 de `86006000`; Las Olas Blvd y Broward Blvd "no se cruzan, a 292 m". Después el Censo bloqueó la IP (HTML "Request Rejected"); con la corrección la búsqueda responde 200 con el cruce del FDOT y el Censo marcado como caído.
Notas: B-15 abierto del lado del Censo (se levanta solo). SPEC-B14 puntos 9, 12 y 13, CA-20 a CA-22; API.md y ARQUITECTURA actualizados. Sin commit.

## 2026-10-31 10:58 -05:00 Trazo ajustado a la LRS del FDOT (PEN-35)

Estado: terminada
Cambios: `MapTrace.input_length_mi`; longitudes de filas y total desde las LineString LRS oficiales; prueba de la regla geométrica y del contrato de trazo. SPEC-B14, API y el backlog actualizados.
Evidencia: 189 pruebas de backend, Ruff y formato limpios; ver `calidad/RESULTADOS.md`.
Notas: no se implementó enrutamiento ni se cambió ninguna escritura o configuración de Smartsheet.
Entrega: commit local `d091361` creado. El `git push` del 2026-10-31 10:59 -05:00 no llegó a GitHub porque el entorno no dispone de credenciales; queda pendiente de una sesión autenticada.

## 2026-10-31 11:30 -05:00 Integridad del trazo (PEN-37)

Estado: terminada
Cambios: `lrs_slicing.py` une fragmentos contiguos por M/posición; `map_rules` corrige escala de longitud por latitud; `trace_rules` separa salidas/regresos y estima cobertura. Contrato con porcentaje, distancia sin vía y longitudes desconocidas en `null`. B-16, specs, API, arquitectura y plan de calidad sincronizados (PY-01, PY-14, PY-21).
Evidencia: 205 pruebas, Ruff y formato; GET reales de control, inverso y salida/regreso, detallados en RESULTADOS. El trazo parcial real tiene 57.2 % asociado y 0.380 mi sin vía dentro del radio.
Límite: no se verificó el algoritmo de OSP con los mismos vértices; la evidencia anterior del control era reconstrucción desde medidas, precisada en SPEC-B14 y GIS_PUBLICO_FLORIDA. No se tocó configuración ni datos de Smartsheet.
Entrega: commit local `a02cd17`; `git push` falló por falta de credenciales HTTPS en esta sesión (`could not read Username`). Pendiente subir desde una sesión autenticada.

## 2026-10-31 12:40 -05:00 Cierre del ajuste automático (PEN-38) y cruces recortados (PEN-39)

Estado: terminada
Cambios: PEN-38 llegó implementada y en curso en el commit `d2c9999` (grafo LRS local, búsqueda del recorrido, respaldo estricto y avisos); se verificó con datos reales y se cerró. PEN-39: `map_query.crossing_filters` reintenta sin el tipo de vía final y `StreetFinder._fdot_crossings` lo aplica a la calle que cruza y a la vía, sin repetir vías probadas. SPEC-B14 (capa 6 y punto 9, CA-29), REQUERIMIENTOS, plan de calidad y RESULTADOS actualizados.
Evidencia: 220 pruebas, Ruff y formato limpios. Lecturas reales del GIS del FDOT detalladas en `calidad/RESULTADOS.md`: control exacto, desplazamientos lateral de 45–50 m corregidos, diagonal reconstruida en dos filas y "Federal Hwy & Sunrise" encontrado.
Límite: sigue sin compararse con OSP usando los mismos vértices (OSP-PEN-01); las conexiones entre vías son geométricas, no confirman giros ni pasos a desnivel. Sin lecturas ni escrituras de Smartsheet.
## 2026-11-03 10:11 -05:00 Plan de servicios futuros (PEN-24)

Estado: documentado, sin implementar.
Cambio: ampliado PEN-24 con el plan de IDs, catálogos, selectores, validación y supervisión, y una base mínima de estado operativo para el servicio futuro. Detalle y fases en `future_docs/SERVICIOS_SMARTSHEET_BD.md`.
Evidencia: revisión de documentación y del texto proporcionado por el usuario; sin pruebas ni acceso a Smartsheet. El panel sigue sin base de datos y en modo solo lectura.

## 2026-11-03 10:13 -05:00 Esquema PostgreSQL para IDs (PEN-24)

Estado: esquema preparado; instalación en Windows y servicio pendientes.
Cambios: ADR-B18, dos tablas y guía de instalación en `servicios/ids/`; panel y modo solo lectura sin cambios.
Evidencia: PostgreSQL 18 temporal ejecutó el esquema y aceptó una reserva sintética; rechazó número duplicado y ámbito inexistente. Sin acceso a Smartsheet.

## 2026-11-03 10:20 -05:00 Base PostgreSQL creada en Linux (PEN-24)

Estado: base y esquema creados; servicio y usuario de aplicación pendientes.
Evidencia: el usuario ejecutó el esquema y compartió `COMMIT` y la salida de `\dt` de `galp_servicios` con `secuencia_id` y `asignacion_id`, ambas propiedad de `postgres`. No se verificó conexión propia ni se accedió a Smartsheet.

## 2026-11-03 10:23 -05:00 Validación de asociaciones (PEN-24)

Estado: implementada en solo lectura; configuración del piloto pendiente.
Cambios: SPEC-B15, endpoint y reglas de asociaciones con catálogo configurable, y regla de escritura exclusiva para workspace `Pruebas` (PY-21, SM-02, ADR-B11). Catálogos, IDs y selectores no implementados.
Evidencia: 222 pruebas aprobadas, Ruff y formato correctos. Consultas GET reales identificaron las cuatro hojas y sus columnas; comparación tentativa de Tareas contra Proyectos con 2 referencias desconocidas, sin confirmar aún que las columnas elegidas representen la relación correcta. Ninguna escritura.

## 2026-11-03 10:39 -05:00 Motor de reservas de IDs (PEN-24)

Estado: motor independiente y plan puro de catálogo implementados; integración real incompleta.
Cambios: reglas de formato, inicialización atómica, transacciones, auditoría e idempotencia; migración 002 preparada sin aplicar; relación principal y workspace confirmados por el usuario. SPEC-ID01 y SPEC-B15 actualizadas.
Evidencia: 226 pruebas, Ruff y formato aprobados; pruebas concurrentes en PostgreSQL temporal. Lecturas GET del piloto: 19 IDs visibles canónicos, 6 relaciones principales revisadas sin problemas. No se conocen máximos de filas eliminadas; sin inicializar base real ni escribir en Smartsheet.

## 2026-11-03 10:45 -05:00 Preparación de integración de IDs (PEN-24)

Estado: parcial; migración e importación reales, conector y ejecución DRY_RUN pendientes.
Cambios: validación de inventario, carga opcional de máximos históricos conocidos, reglas puras de simulación y recuperación, script de respaldo y migración 002. Escritura remota bloqueada hasta resolver concurrencia y verificación de workspace.
Evidencia: 229 pruebas aprobadas, Ruff, formato y sintaxis shell correctos. GET reales: 19 IDs validados en memoria, 38 consultas de historial a celdas de las cuatro hojas sin fallos; 55 hojas candidatas fuera del piloto inspeccionadas en lectura, con 21 120 valores canónicos y 785 otros. No se garantizan máximos históricos ni se importaron datos o escribieron hojas. `sudo` interactivo necesario para migrar la base existente.

## 2026-11-03 10:46 -05:00 Corrección del script de migración (PEN-24)

Estado: corregido; ejecución de migración pendiente.
Evidencia: usuario reportó respaldo creado y error de permiso al leer SQL como `postgres`; el script ahora redirige el SQL leído por el usuario a `psql`. `bash -n` y `git diff --check` aprobados. No se afirma ejecución de la migración.

## 2026-11-03 10:47 -05:00 Migración PostgreSQL aplicada (PEN-24)

Estado: terminada según salida aportada por el usuario; inicialización pendiente.
Evidencia: script informó respaldo creado e índice legible, `BEGIN`, dos `CREATE TABLE`, `COMMIT` y listado de las cuatro tablas de `galp_servicios`. No se probó restauración completa ni conexión propia, y no se importaron IDs ni se escribieron hojas.

## 2026-11-03 11:00 -05:00 Importación y simulación de IDs (PEN-24)

Estado: implementación probada; usuario de aplicación e importación real pendientes de acceso sudo.
Cambios: importación repetible que valida relaciones, workspace y versiones; CLI DRY_RUN con proyección en memoria; reservas deshabilitadas por defecto; script para rol PostgreSQL de permisos limitados. No se habilitaron escrituras en Smartsheet.
Evidencia: 233 pruebas aprobadas, Ruff y formato; GET reales confirmaron workspace, 19 IDs y sus relaciones. Respaldo previo a 002 restaurado en instancia PostgreSQL temporal: dos tablas originales presentes. Sin prueba de restauración de un respaldo posterior a 002. `sudo -n` requiere autenticación; no se creó rol ni se inicializó la base real.

## 2026-11-03 11:02 -05:00 Importación del piloto a PostgreSQL (PEN-24)

Estado: importación terminada; generación automática y escrituras remotas deshabilitadas.
Evidencia: usuario creó rol `galp_ids`; conexión confirmó ausencia de superusuario, creación de roles, bases y replicación, y ausencia de DELETE sobre asignaciones. Dos ejecuciones de importación: 19 asignaciones confirmadas, 12 secuencias, 19 eventos de inicialización, sin IDs duplicados. DRY_RUN: 19 ya estables, sin cambios. Reserva histórica incompleta; no hay garantía sobre números eliminados antes del inventario. Sin escrituras en Smartsheet.
Configuración: se detectó `APP_READ_ONLY=false` en configuración local y se cambió a `true` conforme a la instrucción del usuario; no había servidor en 8710 ni archivo de puerto activo.

## 2026-11-03 11:15 -05:00 Simulación de tareas nuevas (PEN-24)

Estado: implementada en solo lectura; integración de escritura pendiente.
Cambios: DRY_RUN proyecta ID cuando la fórmula de tarea está pendiente, reutiliza reservas por fila y exige padre confirmado en Smartsheet y PostgreSQL; discrepancias en referencias o fórmula se reportan. Prioridad incremental y política histórica propuesta en SPEC-ID01 y README.
Evidencia: 11 pruebas específicas y 234 de backend aprobadas, Ruff y formato correctos; DRY_RUN real leyó 19 IDs ya estables. Sin reservas nuevas ni escrituras en Smartsheet.

## 2026-11-03 11:55 -05:00 Coordinación de IDs y recuperación (PEN-24)

Estado: coordinador probado con adaptador simulado; escritura real bloqueada.
Cambios: confirmación idempotente auditada, migración 003 preparada y coordinador con verificación de workspace, lista de hojas, fórmula y reserva; relee tras respuesta incierta. Falta adaptador remoto con escritura condicional atómica comprobada y aplicar 003.
Evidencia: 15 pruebas específicas aprobadas con PostgreSQL temporal, incluyendo concurrencia, fallos de red y recuperación; Ruff y formato correctos. Ninguna escritura en Smartsheet ni migración de la base real.

## 2026-11-04 11:37 -05:00 Integración HTTP del ID Manager (PEN-24)

Estado: consultas y simulación operativas; escritura real y procesador de escritura pendientes.
Cambios: seis endpoints autenticados; monitor opcional de simulación con bloqueo PostgreSQL; adaptador, política configurable y prueba manual preparados con barreras de solo lectura. SQL 003 y script con respaldo y restauración preparados; falta sudo interactivo para aplicarlos. Sin prueba E2E de escritura ni OAuth (PEN-08). Riesgo residual de edición externa simultánea en Smartsheet.
Evidencia: consultas HTTP y `/docs` reales, 19 IDs confirmados, 12 secuencias y 19 eventos. Monitor temporal activo en solo lectura revisó 19 IDs estables y se detuvo correctamente. Sin escrituras en Smartsheet ni aplicación de 003.

## 2026-11-04 12:14 -05:00 Política anual de IDs (PEN-24)

Estado: implementada y probada; reservas automáticas y escrituras reales deshabilitadas.
Cambios: ámbito por empresa, cliente y año de `Date Received`; inicio 001 para años nuevos desde 2027, secuencias existentes preservadas, tareas y solicitudes por padre. Sin inicio implícito para ámbito histórico sin secuencia; fechas tomadas del valor ISO de Smartsheet (PY-21, SM-03).
Evidencia: 289 pruebas backend aprobadas, Ruff y formato correctos; DRY_RUN real reconoció 19 IDs estables. Base real: 19 asignaciones, 12 secuencias, 19 eventos; migración 003 pendiente. Sin escritura en Smartsheet. Historial de filas eliminadas previo a la adopción sigue incompleto.

## 2026-11-04 12:17 -05:00 Preparación del procesador secuencial (PEN-24)

Estado: reglas de procesamiento probadas, ejecución real bloqueada por OAuth y autorización.
Cambios: los candidatos se ordenan por dependencia, el DRY_RUN detecta proyectos sin fórmula y usa la política histórica, y la prueba manual rechaza escrituras mientras falte OAuth. No se conecta el procesador de escritura ni se habilita el modo de escritura.
Evidencia: 289 pruebas backend aprobadas con Smartsheet simulado, PostgreSQL temporal, Ruff y formato. DRY_RUN real de lectura: 19 IDs estables. Sin nuevas reservas ni escrituras en Smartsheet.

## 2026-11-03 18:31 -05:00 Calles de St. Johns y lugares censales (PEN-40)

Estado: terminada.
Pedido: el usuario vio limitada la información del mapa en St. Johns County. La documentación de mapas sólo cubría Broward, Palm Beach, Martin y Miami-Dade.
Hallazgos (GET reales sin sesión): FDOT y FDACS sí responden en St. Johns (condado 78, Distrito 2, DOR 65), pero la LRS no trae calles locales y la capa 7 de `Admin_Boundaries` hacía pasar lugares censales (Nocatee, World Golf Village; `CLASSFP` U2) por ciudades. El condado publica `Road/MapServer/36` con `MAINTENANCE` (MJ-SJ-01 a MJ-SJ-10).
Cambios: `services/county_roads.py` (adaptador M5), `gis/layers.stjohns_roads`, `gis_stjohns_roads_url`, `MapLocation.place`, ciudad sólo con `CLASSFP` C1, catálogo de fuentes en `services/map_sources.py`; SPEC-B14, REQUERIMIENTOS y `future_docs/MAPAS_JURISDICCION_PARCELAS.md` actualizados.
Evidencia: ver RESULTADOS de la misma hora. Modo solo lectura sin cambios; sin escrituras en Smartsheet.

## 2026-11-03 19:09 -05:00 Calles por jurisdicción y permisos (PEN-41)

Estado: terminada.
Pedido: el usuario mostró capturas de Google Earth (trazo por CR 210 W hacia Harbor Chase of Beach Walk) y del iMAP del condado: ni el GIS ni el tasador colorean las calles por responsable ni dicen qué permiso pedir. Después pidió separar en condado, village, city y Estado.
Cambios: `GET /api/map/streets` y `GET /api/map/trace/streets` (`services/county_streets.py`, `services/trace_streets.py`), adaptador con rectángulo y `classify`, `valid_trace_path` y `trace_rules.kept_groups` reutilizables; `MapLocation.municipality_type` y autoridades `TOWN` y `VILLAGE` desde `LSAD`; el condado se nombra "X County". SPEC-B14, REQUERIMIENTOS y MJ-SJ-11 actualizados.
Evidencia: ver RESULTADOS de la misma hora. Modo solo lectura sin cambios.

## 2026-11-04 15:29 -05:00 Escritura controlada y procesador del ID Manager (PEN-24)

Estado: implementado y probado sin escrituras reales; prueba real preparada, pendiente de autorización.
Pedido: continuar el ID Manager: conector conectado al coordinador, recuperación, procesador periódico deshabilitado, endpoints de Swagger y prueba integral sin escrituras. El usuario confirmó que la migración 003 está aplicada y que OAuth no es requisito del piloto.
Cambios: `runtime.py` con barreras y ensamblaje; prueba manual sin bloqueo OAuth y reutilizable desde `POST /rows/assign`; procesador con tope por ciclo, resultados por fila y ciclo a demanda con bloqueo global; `GET /audit` y `GET /recovery`; Stable ID sin registro en PostgreSQL ahora es conflicto (ID-27); DRY_RUN en orden de fórmula (ID-28). Riesgo de numeración por fórmulas que cuentan filas documentado para decisión (ID-31).
Evidencia: ver RESULTADOS de la misma hora. Sin escrituras en Smartsheet ni cambios en PostgreSQL real; `APP_READ_ONLY=true`.

## 2026-11-04 16:36 -05:00 Numeración desde Smartsheet y primera escritura real (PEN-24)

Estado: terminado para el piloto; activación permanente del procesador pendiente de decisión del usuario.
Pedido: el usuario indicó que todo el piloto es de prueba y autorizó ediciones; pidió conservar los IDs, evitar conflictos, que Smartsheet genere la numeración y que lo que no tenga rastro se cree o registre en la base.
Cambios: reserva con número preferido de la fórmula, ámbito sin rastro desde 1, registro de Stable ID existente, restauración de Stable vaciado, ID confirmado permanente, `Reference` vacía aceptada, acción `pending_data` y campo `renumbered` (SPEC-ID01 ID-32 a ID-35).
Evidencia: ver RESULTADOS de la misma hora. Escrituras sólo en la columna Stable ID de cuatro filas de Pruebas; `backend/.env` sin cambios y en solo lectura.

## 2026-11-04 16:48 -05:00 Activación del procesador automático de IDs (PEN-24)

Estado: configurado; pendiente de reinicio del backend por el usuario.
Pedido: el usuario decidió activar el procesador tal como está; nadie usará el panel por ahora y la separación de `APP_READ_ONLY` se revisará al final.
Cambios: `backend/.env` con `APP_READ_ONLY=false`, `IDS_WRITES_ENABLED`, `IDS_TRANSITION_APPROVED`, `IDS_PROCESSOR_WRITES_ENABLED` e `IDS_MONITOR_ENABLED` en `true`; intervalo 60 s y máximo 5 filas por ciclo. AGENTS.md y SPEC-ID01 ID-36 actualizados.
Evidencia: `Settings` lee las cuatro barreras activas. Sin escrituras nuevas en Smartsheet al configurar.

## 2026-11-04 16:56 -05:00 Selectores de Linked Tracking por cliente (PEN-24, SPEC-B16)

Estado: backend implementado y probado; hoja catálogo y desplegable vinculado pendientes de autorización y prueba en la interfaz.
Pedido: que Customer determine qué proyectos se pueden elegir en Linked Tracking, priorizando capacidades nativas y conservando históricos.
Hallazgos: desplegables vinculados nativos con filtro estático de una condición; dependientes por fila "In Planning"; formularios y Dynamic View no cambian opciones por fila; Customer tiene 11 clientes y Linked Tracking ya es desplegable estático con dos históricos.
Cambios: opciones de desplegable en `RawColumn`; `catalog_rules`, `project_catalog`, `catalog_sync`, rutas `/api/catalogs`; ajuste `APP_PROJECT_CATALOG_SHEET`; sincronización opcional al final del ciclo del procesador.
Evidencia: ver RESULTADOS de la misma hora. Sin escrituras en Smartsheet.

## 2026-11-04 17:00 -05:00 Procesador automático verificado (PEN-24)

Estado: en operación en Pruebas.
Pedido: el usuario reinició el servidor y pidió probarlo.
Evidencia: ver RESULTADOS de la misma hora. El procesador asignó sin intervención la fila de Records creada por el usuario (`KMV-CC-26-720-01-R1`); no hubo conflictos ni escrituras fuera de la columna Stable ID.

## 2026-11-04 17:07 -05:00 Hoja catálogo creada y sincronizada (PEN-24, SPEC-B16)

Estado: catálogo en operación; vínculo del desplegable pendiente de configuración manual en la interfaz.
Pedido: el usuario autorizó crear todo lo necesario para el selector de Linked Tracking.
Cambios: hoja catálogo en Pruebas, `APP_PROJECT_CATALOG_SHEET` en `.env`, orden por cliente tras sincronizar.
Evidencia: ver RESULTADOS de la misma hora. Sin cambios en Proyectos, Tareas, Records, Revisiones ni PostgreSQL.

## 2026-11-04 17:24 -05:00 Selector de Linked Tracking en operación (PEN-24, SPEC-B16)

Estado: en operación en Pruebas; comprobación visual del filtrado pendiente del usuario.
Pedido: el usuario vinculó el desplegable y autorizó crear lo necesario para probar.
Cambios: fila de prueba `PRUEBA - catálogo automático` en Proyectos (Pruebas), identificable y desechable; consume `KMV-OT-26-002`.
Evidencia: ver RESULTADOS de la misma hora.

## 2026-11-04 17:31 -05:00 Prueba visual del selector de Linked Tracking (PEN-24, SPEC-B16)

Estado: comportamiento esperado; resaltado en rojo pendiente de configurar en la interfaz.
Pedido: el usuario eligió un proyecto CC en una fila BS y pidió marcarlo en rojo.
Evidencia: fórmula `ERROR: DIFFERENT CUSTOMER` en la fila 4 y `other_customer` en `/api/catalogs/linked-tracking` (sólo lecturas). Sin escrituras.

## 2026-11-04 19:33 -05:00 Puesta al día del equipo Windows (PEN-24)

Estado: terminada.
Pedido: el usuario pidió `git pull`, retomar y hacer desde el equipo Windows todo lo posible; actualizó el `.env` de este equipo.
Hallazgos: el `.env` de Windows tiene las barreras del ID Manager y la hoja catálogo, pero este equipo no tiene PostgreSQL (B-16). Varias líneas de REQUERIMIENTOS, AGENTS y `servicios/ids/README.md` seguían describiendo el ID Manager sin escrituras ni OAuth resuelto.
Cambios: dependencias del entorno local; B-16; estado de PEN-06 y PEN-24 y resumen de pendientes; estado en AGENTS; README del servicio con la regla de un solo procesador; SPEC-B16 LB-15.
Evidencia: ver RESULTADOS de la misma hora. Sin escrituras en Smartsheet ni en PostgreSQL.

## 2026-11-05 00:09 -05:00 Resaltado en rojo de Linked Tracking (PEN-24, SPEC-B16)

Estado: terminada.
Pedido: crear en la interfaz el formato condicional del error de cliente (LB-14).
Cambios: el usuario creó la regla en Proyectos (Piloto) con condición en `Control Linked Tracking`, tras corregir la columna de la condición (había elegido Linked Tracking). SPEC-B16 LB-16, REQUERIMIENTOS y SBD-14 actualizados.
Evidencia: confirmación del usuario de que funciona; no se volvió a leer la hoja. Sin escrituras del servicio.

## 2026-11-10 10:00 -05:00 ID Manager sobre Presentable (PEN-24)

Estado: código y pruebas listos; reinicio a 001 pendiente de ejecución por el usuario (sudo).
Pedido: trabajar sólo en Presentable, olvidar las hojas anteriores, tolerar cambios de nombre o carpeta, sin IDs propios para filas hijas y renumerar los ejemplos desde 001. El usuario aclaró que las filas hijas llevan el mismo ID que su madre.
Cambios: `parent_id` en filas; `pilot.py` con Presentable y consulta en cada llamada; madres numeradas, hijas con el ID de su madre (`child_fill`), catálogo sólo con madres y empresa por defecto; conflicto anticipado para IDs ya registrados; `servicios/ids/reiniciar_registro.py`.
Evidencia: ver RESULTADOS de la misma hora. Sin escrituras.

## 2026-11-10 10:07 -05:00 Reinicio a 001 en Presentable (PEN-24)

Estado: preparado; falta encender el backend para asignar.
Pedido: renumerar el ejemplo de Presentable desde 001 olvidando las hojas anteriores.
Cambios: el usuario reinició el registro con sudo; luego se vaciaron los Stable IDs de Presentable, se limpió el catálogo y se agregó `Control Linked Tracking`.
Evidencia: ver RESULTADOS de la misma hora.

## 2026-11-10 10:14 -05:00 Ejemplo de Presentable desde 001 (PEN-24)

Estado: IDs y catálogo terminados; vínculo del desplegable y regla roja pendientes en la interfaz.
Evidencia: ver RESULTADOS de la misma hora. Hallazgo: el desplegable de Presentable es una lista fija copiada, no vinculada.

## 2026-11-10 10:20 -05:00 Desplegable de Presentable vinculado (PEN-24, SPEC-B16)

Estado: terminado; regla roja pendiente de confirmar por el usuario.
Evidencia: ver RESULTADOS de la misma hora. Sin escrituras del servicio.

## 2026-11-10 10:52 -05:00 Flujo madre/hija comprobado en Presentable (PEN-24)

Estado: terminado.
Pedido: el usuario pidió confirmar y probar el flujo de crear madre, insertar hija e indentar.
Evidencia: ver RESULTADOS de la misma hora. Quedan tres filas `PRUEBA` en Presentable; el ID `KMV-BS-26-003` queda consumido.

## 2026-11-10 11:38 -05:00 Madres copiadas reciben el siguiente número (PEN-24)

Estado: implementado y probado con simulación; pendiente la prueba en vivo del usuario.
Pedido: que copiar y pegar una madre continúe la numeración sin repetir IDs.
Cambios: `update_stable_id_once` con valor esperado; detección `renumber_copy` en el DRY_RUN; `IdConnector.renumber_copy`; procesador y recuperación (SPEC-ID01 ID-42).
Evidencia: ver RESULTADOS de la misma hora.

## 2026-11-10 12:26 -05:00 Copia en vivo y reacción en segundos (PEN-24)

Estado: terminado; pendiente que el usuario mida el tiempo con una nueva copia.
Pedido: reaccionar al instante al copiar y pegar una madre.
Cambios: consulta de versión entre ciclos y ciclo inmediato tras escribir (SPEC-ID01 ID-43); `IDS_MONITOR_POLL_SECONDS`.
Evidencia: ver RESULTADOS de la misma hora.

## 2026-11-10 12:47 -05:00 Reportes de Presentable (PEN-42)

Estado: terminado; filtros deducidos pendientes de confirmar por el usuario.
Pedido: reportes por persona (todo el equipo), MOT y paquetes de Carlos y German, invoices y All Records Request, enlazados a Presentable.
Cambios: cuatro reportes en `Pruebas/Producto` y columna `Invoice Status` en Presentable. Todo en Pruebas.
Evidencia: ver RESULTADOS de la misma hora.

## 2026-11-10 12:52 -05:00 Hojas de soporte movidas a Producto (PEN-24, PEN-42)

Estado: terminado.
Pedido: el usuario renombró Presentable a `PROJECT KMV` y los reportes (All Records Request, Invoices, MOT y Paquetes, Permitting) y pidió traer el catálogo y la lista de contactos a la carpeta.
Cambios: `Catálogo de Proyectos (Piloto)` (8048198976491396) y `Contact List` (8285254227021700) movidos a `Pruebas/Producto`; se movieron en lugar de copiarse para conservar sus IDs.
Evidencia: las tres hojas en `Pruebas/Producto`; referencias `Directorio Correo`, `Directorio Nombre` y `Directorio Activo` de PROJECT KMV en estado OK; desplegable Linked Tracking con las opciones del catálogo; correos de Designer1 resueltos en 4 de 4 filas. El ID Manager identifica la hoja por ID (5254686035890052), así que el cambio de nombre no lo afecta.

## 2026-11-10 13:06 -05:00 Lista de clientes para el desplegable Customer (PEN-42)

Estado: hoja creada; vínculo del desplegable pendiente en la interfaz.
Pedido: dejar de usar "Others" y elegir el cliente desde una lista mantenida a mano, vinculada de forma nativa.
Cambios: `Customer List` en `Pruebas/Producto` con los 11 clientes actuales, todos activos. Incidente: la primera creación falló al agregar dos columnas con fórmula en una sola solicitud, pero la hoja ya estaba creada; el reintento creó un duplicado vacío (8890058024374148), que se borró tras comprobar que estaba vacío. Las columnas se agregaron de a una.
Evidencia: 11 filas con `Code` calculado, `Active` marcado y `Check` vacío.

## 2026-11-11 09:32 -05:00 Columna Closed dinámica en PROJECT KMV (PEN-27)

Estado: terminado; filtro de la Dynamic View pendiente en la interfaz y clasificación pendiente de aprobación.
Pedido: retomar el trabajo de otro chat (pull) y que la vista de Permitting Team / Permit Coordinator cambie sola según el estado.
Hallazgo: la referencia `Project Status Catalog Closed` no existía; `Closed` quedaba en falso para todo estado.
Cambios: referencia creada por API en PROJECT KMV (Pruebas). Prueba con cambios temporales de `Project Status` en una fila hija vacía, restaurada al final.
Evidencia: cerrados `COMPLETE` y `4. Permit Expired`; abiertos `4. Permit is Required`, `4. Permit Approved` y vacío; tras crear la referencia el cálculo es inmediato.

## 2026-11-11 09:50 -05:00 Email Permitting y aviso de asignación (PEN-42)

Estado: columna creada; automatización pendiente en la interfaz.
Pedido: columna y automatización para Permitting Team, con nombres en inglés.
Cambios: `Email Permitting` en PROJECT KMV (índice 67) con la misma fórmula del Directorio que `Correo Designer1`. Intento de crear la regla desactivada por API: rechazado (422, el método POST no existe); no se creó nada.
Evidencia: en las filas actuales se resuelve el correo de Carlos Lopez; Daniel Zuñiga y Giuliano Leon Jr. quedan vacíos por faltar en el Directorio.

## 2026-11-11 12:20 -05:00 Dynamic View KMV - PERMITS filtrada por Closed (PEN-27)

Estado: configurado por el usuario; prueba visual con una fila cerrada pendiente.
Cambios (interfaz, por el usuario): filtro de hoja `Open` en PROJECT KMV (compartido, `Closed` sin marcar) y `Settings > General > Restrict view by sheet filter` de la vista KMV - PERMITS apuntando a ese filtro. Automatizaciones `DV | New Task Designer1`, `Designer2` y `Permitting Team` creadas por el usuario, desactivadas al revisarlas.
Evidencia: por API (`include=filterDefinitions`) el filtro `Open` es SHARED, AND, `Closed` IS_UNCHECKED. Hallazgo: el filtro de filas de Dynamic View no está en `View Display` ni en `Details Panel`, sino en `General` y se basa en un filtro compartido de la hoja.

## 2026-11-11 16:18 -05:00 Revisión de Project Status Catalog y Closed en PROJECT KMV (PEN-27)

Estado: Dynamic View KMV - PERMITS comprobada por el usuario (la fila cerrada desaparece); revisión sólo con GET, sin escrituras.
Evidencia: catálogo `Project Status Catalog` (6541648290074500) con 61 estados, sin repetidos ni espacios sobrantes, compartido sólo con su propietario. PROJECT KMV: `Phase` y `Closed` son fórmulas de columna con `@row` (cada fila depende sólo de su propio `Project Status`); las 3 referencias al catálogo en estado OK; filtro `Open` SHARED, `Closed` IS_UNCHECKED, sin incluir madres. Las 60 opciones reales de `Project Status` están en el catálogo; las 9 opciones separadoras (`----`) no, y quedan abiertas; `4. Permit-Awaiting Payment` está en el catálogo pero no en el desplegable. Fila hija con `COMPLETE` marcada como cerrada y su madre abierta: cada fila se filtra por separado. Automatizaciones `DV | New Task` (Designer1, Designer2, Permitting Team) ahora activas. Del equipo de Permitting Team, 6 de 13 opciones tienen correo activo en Contact List.
Pendiente: los reportes de PEN-42 siguen filtrando con la lista `APP_CLOSED_STATUSES` y no coinciden con `Closed` (cambiarlos a `Closed` sin marcar en el Report Builder); `Phase` vacía para estados sin número; aprobación de la clasificación (PEN-27); correos faltantes del directorio; opcional: vincular el desplegable `Project Status` al catálogo para mantener una sola lista.

## 2026-11-11 16:45 -05:00 Project Status vinculado al catálogo y cierre de sesión (PEN-27, PEN-43, PEN-44)

Estado: PEN-27 en curso; PEN-43 propuesta en espera del reparto de estados; PEN-44 consulta respondida sin decisión.
Cambios: el usuario vinculó `Project Status` de PROJECT KMV a `Project Status Catalog` / `Status` (sin filtro, "Limit to list values only") y quitó del catálogo `4. Permit-Awaiting Payment`. Backend detenido a pedido del usuario (puerto 8710 libre); lo encenderá él desde su terminal. Docs: PEN-27 con hecho y faltantes, nuevas PEN-43 y PEN-44, resumen del backlog y estado de AGENTS.md.
Evidencia (sólo GET): columna `Project Status` con 60 opciones iguales a los 60 estados del catálogo, `validation` true y sin separadores; valores de las 9 filas conservados y `Closed` coherente (`8. Process completed` marcado).
Siguiente: que el usuario confirme el reparto de estados por equipo y que gane el estado de permisos (PEN-43); después, con autorización expresa, crear casillas y columnas por API.
