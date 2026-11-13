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

## 2026-11-11 17:47 -05:00 Capacidad de la hoja maestra (PEN-45)

Estado: consulta respondida; decisión pendiente del usuario.
Evidencia: límites oficiales de Smartsheet (500 000 celdas, 20 000 filas, 400 columnas; reportes hasta 50 000 filas). PROJECT KMV tiene 139 columnas (lectura por API de esta sesión): unas 3 597 filas como máximo. Con 3 000 filas por año, un año ocupa el 83 %. Recomendación registrada en PEN-45: hoja activa más archivo por año.

## 2026-11-12 12:14 -05:00 Decisión: una maestra por año (PEN-45)

Estado: decidido por el usuario; falta planificar e implementar.
Cambios: PEN-45 con la decisión y la lista de tareas (regla de ubicación por `Date Received`, creación anual, ID Manager con varias maestras, `Control Linked Tracking` contra `Project List`, capacidad).
Hallazgo: el repositorio git local tiene 7 objetos vacíos, entre ellos el commit de HEAD (`67bc4fa`, del 2026-11-11 19:09, ya enviado a origin), por un apagado inesperado del equipo; los archivos de trabajo están intactos. No se reparó sin autorización del usuario.

## 2026-11-12 13:30 -05:00 Reparación de git y conversaciones copiadas a Obs (PEN-46)

Estado: implementado y probado con simulación; falta la migración 004 (sudo, la ejecuta el usuario) y la prueba real en PROJECT KMV.
Git: 7 objetos vacíos movidos a un respaldo fuera del repositorio, `git fetch origin` los recuperó y `git fsck` quedó limpio; HEAD `67bc4fa` sano.
Cambios: SPEC-B17; `services/obs/` (reglas, registro y paso del procesador); lectura de conversaciones y escrituras de celda y comentario en el cliente; `last_obs_sync` en `/api/ids/status`; migración `004_obs_comentario.sql` y `aplicar_migracion_004.sh`; `APP_OBS_*` en configuración y `.env.example`; `APP_OBS_SYNC_ENABLED=true` en `.env` por autorización del usuario.
Evidencia: 335 pruebas aprobadas, Ruff y formato correctos; vista previa real sólo con GET (7 filas vigentes con comentarios). Hallazgo: la API lista conversaciones de filas borradas; se filtran con la lista de filas vigentes.

## 2026-11-12 14:41 -05:00 Prueba real de Obs (PEN-46)

Estado: en uso en Pruebas.
Cambios: el usuario aplicó la migración 004 y reinició el backend. PEN-46, SPEC-B17, RESULTADOS y AGENTS.md actualizados.
Evidencia: primera pasada con 61 comentarios copiados en 7 filas de PROJECT KMV y 0 errores; la pasada siguiente no escribió nada; `obs_comentario` con 61 registros; `Obs` leído por API con el texto previo conservado.
Siguiente: el usuario revisa la hoja y limpia los `Obs` con chats de prueba; después PEN-43 (reparto de estados) o PEN-45 (maestras por año).

## 2026-11-12 15:02 -05:00 Títulos de sección `**` en Obs (PEN-46)

Estado: implementado y probado con simulación; falta la prueba real con un chat `**`.
Consulta: `** Renewal` en una fila de PROJECT KMV no lo escribió el servicio; el historial de la celda muestra que se escribió a mano el 2026-11-10 y el servicio sólo agregó las líneas `11.12` y `11.11` encima. En el reporte Tracker 2026 - KMV, 79 de 265 `Obs` tienen `**`, en 76 en la primera línea (lectura por API).
Cambios: SPEC-B17 OB-04, OB-16 y CA-08; `rules.compose` reemplaza `daily_entries` y `merge` (aplica los comentarios uno a uno); pruebas nuevas.
Evidencia: 337 pruebas aprobadas, Ruff y formato correctos; backend recargado sin errores.

## 2026-11-12 15:20 -05:00 Prueba real de títulos `**` y filtro por cliente (PEN-46, PEN-44)

Estado: títulos `**` en uso en Pruebas; guía de filtro por cliente entregada, sin cambios en Smartsheet.
Evidencia: el usuario reinició el backend y escribió un chat `**` y otro normal; la API muestra `Obs` con el título arriba, el mensaje debajo y la sección anterior separada por una línea en blanco. PROJECT KMV: `Customer` desplegable con 11 opciones; un filtro compartido (`Open`).
Siguiente: el usuario arma los filtros por cliente y las Dynamic Views; PEN-43 y PEN-45.

## 2026-11-12 16:05 -05:00 Columnas de contactos para la Dynamic View de clientes (PEN-44)

Estado: columnas y fórmula creadas en Pruebas; falta que el usuario cargue correos reales y configure la vista.
Decisión del usuario: Dynamic View restringida por contactos para clientes y un solo reporte para enviar Excel a pedido, cambiando el `Customer Code`. Todo lo que se cree en Smartsheet va en inglés.
Cambios (API, autorizado por el usuario, hojas comprobadas en Pruebas): `Client Contacts` en `Customer List`; referencias `Customer List Customer` y `Customer List Client Contacts`; `Client Access` con fórmula `INDEX`/`MATCH` en PROJECT KMV (140 columnas). PEN-45 con la capacidad nueva (84 %).
Evidencia: relectura con `level=2`: ambas columnas `MULTI_CONTACT_LIST`, fórmula guardada, 9 filas sin contactos todavía. Automatizaciones leídas: 3 avisos activos en PROJECT KMV, ninguna en `Customer List`; por eso no se probó con correos ficticios.

## 2026-11-12 16:41 -05:00 Separación por cliente: contactos verificados (PEN-44)

Estado: columnas y fórmula funcionando; falta configurar y probar la Dynamic View.
Evidencia (sólo GET, sin imprimir correos): `Customer List` con 2 contactos en BS y 2 en CC; PROJECT KMV: 4 filas BS y 5 filas CC con `Client Access` igual al catálogo; reporte `KMV - Customers` con una sola fuente (PROJECT KMV).
Siguiente: restricción por `Client Access` en la vista de clientes y prueba con otra cuenta.

## 2026-11-12 16:45 -05:00 Vista de clientes sin filtro Open (PEN-44)

Estado: decidido por el usuario.
Cambios: la Dynamic View de clientes sólo se restringe por `Client Access`, sin el filtro compartido `Open` (que oculta las filas con `Closed` marcado); el cliente ve también lo cerrado. PEN-44 actualizada.

## 2026-11-12 16:53 -05:00 Aviso automático al cliente y corrección de New Task Permitting (PEN-44)

Estado: automatizaciones creadas y verificadas; falta la prueba real de envío.
Cambios (conector de Smartsheet, autorizado por el usuario, PROJECT KMV en Pruebas): creada `Client | Status Update` (cambio de `Project Status` a 21 estados del tracker de cliente, condición `Client Access` no vacío, correo en inglés con enlace a la vista de clientes); `DV | New Task Permitting Team` pasa a vigilar `Permitting Team` y `Email Permitting`.
Evidencia: `get_workflows` muestra ambas activas con el árbol esperado; los marcadores `{{Columna}}` quedaron como referencias de columna. Estados tomados del reporte `Tracker 2026 - KMV` (265 filas, 20 estados, 19 en el desplegable; falta `4. Permit-Awaiting Payment`, retirado del catálogo).

## 2026-11-12 17:25 -05:00 Asuntos dinámicos en New Task Designer1 y Designer2 (PEN-44)

Estado: hecho y verificado.
Cambios (conector de Smartsheet, pedido del usuario): asunto `New Task: {Tracking Project} – {Project Name}` en Designer1 y `New Task: {Tracking Project} – {Project Name} – {Agency}` en Designer2; las mismas líneas al inicio del mensaje. Resto del árbol igual.
Evidencia: `get_workflows` muestra ambas activas con los marcadores convertidos en referencias de columna.

## 2026-11-12 17:30 -05:00 Revisión de madres e hijas en PROJECT KMV y requisito de ID por cliente (PEN-47)

Estado: revisión hecha; requisito registrado como PEN-47, pendiente de decisiones.
Evidencia (sólo GET, sin imprimir correos): 12 filas (4 madres, 8 hijas), sin errores de fórmula; ID Manager con 4 `already_stable` y 8 `child_inherited`. Hallazgos en PEN-47: dos hijas de una madre Blue Stream con cliente Hotwire y Crown Castle (heredan ID BS y dan acceso a otro cliente), madre sin nombre, hijas con estados de madre sin `Phase` y un `Linked Tracking` a un ID inexistente de otro cliente.

## 2026-11-12 17:50 -05:00 Tracking Project cambia con el cliente (PEN-47)

Estado: implementado y probado con simulación; falta la migración 005 (sudo, la ejecuta el usuario), el reinicio del backend y la prueba real.
Cambios: SPEC-ID01 ID-44 a ID-48; `services/ids/family.py` y `customer_change.py`; retiro de IDs en `store.py`; acciones `rescope`, `detach_child` y `child_follow`; hija con otro ID toma el de su madre; nota `#internal` y `Linked Tracking` actualizados; `move_row_after` en el cliente; interruptor `IDS_CUSTOMER_CHANGE_ENABLED` (apagado por defecto, activado en `.env`); migración 005 y su script; fórmula `Pending ID` aplicada en PROJECT KMV (la anterior quedó en SPEC-ID01 ID-48).
Evidencia: 342 pruebas aprobadas, Ruff y formato correctos; relectura de la columna `Tracking Project` con la fórmula nueva y valores sin cambios; procesador activo sin errores tras la recarga.

## 2026-11-12 17:58 -05:00 Prueba real: hijas de otro cliente fuera de la jerarquía (PEN-47)

Estado: salida de hijas comprobada; falta el cambio de cliente de una madre.
Evidencia (sólo lectura): las hijas Crown Castle y Hotwire de `KMV-BS-26-008` quedaron como madres con `KMV-CC-26-004` y `KMV-HC-26-001`, nota `#internal` en cada una; `id_retirado` disponible y vacía (migración 005 aplicada); procesador sin errores.

## 2026-11-12 18:04 -05:00 Madre con otro cliente comprobada y notas retiradas (PEN-47)

Estado: PEN-47 comprobada en Pruebas.
Evidencia (lectura por API y PostgreSQL): `KMV-BS-26-008` pasó a `KMV-LP-26-001` con auditoría `retirado`, `reservado` y `confirmado`; las hijas siguieron a su madre (cliente LP e ID nuevo).
Cambios: por pedido del usuario no se escribe nada técnico en la hoja; el servicio ya no deja comentarios `#internal` y se borraron las 3 conversaciones que había creado (filas de `KMV-LP-26-001`, `KMV-CC-26-004` y `KMV-HC-26-001`); relectura sin ninguna. 342 pruebas aprobadas, Ruff y formato correctos.

## 2026-11-12 18:28 -05:00 Prueba real: madre copiada y luego cambiada de cliente (PEN-47)

Estado: correcto según ID-42 e ID-44.
Evidencia (PostgreSQL y API): el usuario copió la madre `KMV-BS-26-009`; la copia recibió `KMV-BS-26-010` (18:21:54 a 18:22:02) porque aún era Blue Stream; al cambiarla a Hotwire se retiró `KMV-BS-26-010` y quedó `KMV-HC-26-002` (18:27:37 a 18:27:45). La captura del usuario era anterior al segundo paso o sin refrescar. Efecto esperado: `KMV-BS-26-010` queda como hueco en la numeración (nunca se reutiliza).

## 2026-11-12 18:32 -05:00 Pending ID inmediato ante IDs que ya no corresponden (PEN-47, ID-49)

Estado: fórmula aplicada en PROJECT KMV; falta que el usuario lo vea en un cambio real.
Cambios: fórmula de `Tracking Project` con comprobación de cliente, de copia (por `Row Order`) y de hija de otro cliente; las hijas muestran el ID de su madre. Fórmula anterior en SPEC-ID01 ID-49.
Evidencia: relectura por API con los 14 valores iguales antes y después y sin errores.

## 2026-11-12 18:36 -05:00 Documentación del estado de PROJECT KMV

Estado: hecho.
Cambios: nuevo `HOJA_PROJECT_KMV.md` (HK-01 a HK-41) con ubicación, catálogos, columnas y fórmulas, automatizaciones, vistas, reportes, lo que hace el servicio, separación por cliente, incoherencias de datos y pendientes; README del backend, AGENTS.md y resumen y estado de PEN-44 en `REQUERIMIENTOS.md` actualizados.
Evidencia (sólo GET): 14 filas (8 madres, 6 hijas), 140 columnas, 8 referencias OK, filtros `Open` y uno personal, catálogos movidos por el usuario a `Producto/List Tools` (Project Status Catalog renombrado a Project Status List) y reportes en `Producto/Reports`.

## 2026-11-12 18:51 -05:00 Análisis de columnas de PROJECT KMV frente a los originales (PEN-45)

Estado: análisis entregado; sin cambios en Smartsheet; falta la decisión del usuario.
Evidencia (sólo GET, conteos sin contenido): originales CC y BS 2026 con 117 columnas, 2 233 y 1 294 filas; 2025 con 2 380 y 1 276; 2024 con 1 378 y 871. Dependencias revisadas: fórmulas de columna, automatizaciones, 5 reportes de `Producto/Reports` y código del backend. 11 columnas sin uso real, 11 de uso mínimo y 6 nuevas por confirmar (detalle en PEN-45).

## 2026-11-12 18:54 -05:00 Documentación al día

Estado: hecho.
Cambios: PEN-45 con la revisión de capacidad (un año no entra con 140 columnas) en su estado y en el resumen del backlog; `HOJA_PROJECT_KMV.md` HK-40 y HK-41 al día; AGENTS.md con el estado de PEN-45 y tres reglas del usuario de esta sesión: todo en inglés en Smartsheet, nada técnico a la vista y commit al terminar cada tarea con push a cargo del usuario.

## 2026-11-12 18:55 -05:00 Consulta: hojas auxiliares para bajar columnas (PEN-45)

Estado: respondida; sin decisión ni cambios en Smartsheet.
Resumen: opciones, costos y recomendación registrados en PEN-45 (quitar columnas primero; Facturación como primera hoja auxiliar si hace falta).

## 2026-11-12 18:59 -05:00 Vista de tabla y hojas a gran escala (PEN-45)

Estado: consulta respondida con la ayuda oficial; sin cambios en Smartsheet.
Resumen en PEN-45: la vista de tabla no amplía el límite; el millón de celdas exige hoja a gran escala (Enterprise), que desactiva grid, automatizaciones y endpoints de la API que usa el servicio. Pista para PEN-43 y SPEC-B16: filtrado dinámico de desplegables vinculados en la vista de tabla, por probar en una copia.

## 2026-11-12 19:00 -05:00 Hoja a gran escala: impacto en la API del servicio (PEN-45)

Estado: consulta respondida; sin cambios.
Evidencia: el cliente implementa `list_columns` con `GET /sheets/{id}/columns` y `get_row` con `GET /sheets/{id}/rows/{rowId}`, los dos no admitidos en hojas a gran escala; búsqueda en `app/`: unas 20 llamadas en 5 módulos. Usuario con plan Enterprise. Registrado en PEN-45 y HK-20.

## 2026-11-12 23:45 -05:00 Consulta: cuántas columnas tener en la maestra (PEN-45)

Estado: recomendación entregada (unas 107 columnas, quitando 33); sin cambios en Smartsheet; falta la decisión del usuario.
Evidencia (sólo GET, desde el equipo Windows): hojas 2026 de Breezeline (38 filas), Lightpath (39), Hotwire (21) y Others (49) que el conteo anterior no incluía; columnas de los 5 reportes de `Producto/Reports`: `Permitting` usa `Runner Pick up` y 9 columnas de días, `Invoices` usa `Aerial`. Detalle en PEN-45.

## 2026-11-13 00:10 -05:00 Consulta: hojas hijas que reciban y devuelvan cambios (PEN-45)

Estado: respondida; sin cambios en Smartsheet ni decisión.
Resumen en PEN-45: ida y vuelta completa no ahorra celdas; diseño en estrella (cada grupo en su hoja, contexto por fórmula en la hija, como mucho una columna resumen en la maestra) y limpiar las 33 columnas primero.

## 2026-11-13 00:30 -05:00 Análisis de uso de columnas con todos los clientes (PEN-45)

Estado: análisis entregado en `ANALISIS_COLUMNAS_KMV.md`; sin cambios en Smartsheet; el usuario decide antes de quitar nada.
Evidencia (sólo GET, sólo conteos, script temporal fuera del repo con el cliente del backend): 12 hojas originales (2025: 3 938 filas con datos; 2026: 3 634 al 12-nov, 1 423 madres y 2 211 hijas), 140 columnas de PROJECT KMV con fórmulas, 5 reportes, 6 automatizaciones y búsqueda en el código del backend (`Project Number`, `Frozen Number` y `Designers List` no se usan). El usuario indicó que el metraje lo llena diseño, o facturación si los jefes lo deciden.

## 2026-11-13 09:10 -05:00 Verificación del análisis de columnas desde el equipo Linux (PEN-45)

Estado: verificado; sin cambios en Smartsheet.
Cambios: `git pull` de 3 commits del equipo Windows (f2760c2, ea63cac, effb687); AC-27 y AC-28 en `ANALISIS_COLUMNAS_KMV.md`; PEN-45 marca como superado el análisis del 2026-11-12 18:51; HK-20 y AGENTS.md con las cifras de los 6 clientes.
Evidencia (sólo GET, conteos): 12 hojas originales 2025 y 2026 (2025: 3 939 filas; 2026: 3 638, 1 427 madres y 2 211 hijas); porcentajes de 10 columnas iguales al documento salvo `Aerial` 2025 (ceros); alcance de los reportes `Permitting` y `MOT y Paquetes` leído con `include=scope`: PROJECT KMV.

## 2026-11-13 09:25 -05:00 Columnas sin uso real en 2026 y propuesta de Records aparte (PEN-45)

Estado: medición y opinión entregadas; sin cambios en Smartsheet; falta la decisión del usuario.
Evidencia (sólo GET, conteos): 2026 de CC, BS y Others, 3 552 filas reales; la fila 1 de cada hoja es de ejemplo (114 a 117 columnas llenas) y se excluyó; 9 columnas sin ningún valor real. Detalle en AC-29 a AC-32.
- Propuesta adicional del usuario (2026-11-13 09:25): Facturación en hoja aparte con un aviso en la maestra; registrada en AC-33 y AC-34.

## 2026-11-13 09:50 -05:00 Hoja de trabajo nueva y hojas hijas (PEN-48, PEN-49)

Estado: pendientes registrados; plan propuesto; sin cambios en Smartsheet ni en el servicio.
Evidencia (sólo GET): copia `PROJECT KMV 1.0.0` en Pruebas con 140 columnas, 14 filas y los mismos Stable IDs; faltan 2 automatizaciones de `LT Records`; 68 comentarios copiados con ids nuevos (la original tiene 113 en 50 filas, contando filas borradas). Las de uso mínimo se quedan por ahora (decisión del usuario).

## 2026-11-13 09:59 -05:00 Hoja maestra trasladada a PROJECT KMV 1.0.0 (PEN-48)

Estado: hecho en el servicio; falta que el usuario arranque el backend y apunte reportes y vistas a la copia.
Cambios: `IDS_MASTER_SHEET_ID` (SPEC-ID01 ID-50), `services/ids/rehome.py`, `servicios/ids/mover_hoja_maestra.py`, 4 pruebas nuevas; backend detenido por el asistente; traslado con respaldo `~/galp_backups/mover_hoja_20261113_095906.json`; `.env` con la hoja nueva. PEN-49: `Designer2` pasa a Records; se suman `Date Received` y `Record # Days`.
Evidencia: 346 pruebas aprobadas, Ruff y formato correctos; base con 8 asignaciones en la copia y 7 en la anterior, 68 comentarios marcados; simulación del procesador sobre la copia sin pendientes; Obs sin pendientes.

## 2026-11-13 10:10 -05:00 Hoja hija de Records (PEN-49, SPEC-B18)

Estado: implementada y activada en `.env`; falta reiniciar el backend y la prueba real del usuario.
Cambios (autorizados por el usuario): hoja `Records Requests` en `Pruebas/Producto/PROJECT KMV` y casilla `Records Needed` en la maestra, creadas por API; SPEC-B18; `services/records/`; paso aislado en el procesador; `last_records_sync`; `APP_RECORDS_SYNC_ENABLED` y `APP_RECORDS_SHEET_ID` en `.env`.
Evidencia: 352 pruebas aprobadas, Ruff y formato correctos; relectura de la hoja nueva; vista previa real sin escrituras (14 filas, ninguna marcada). El backend arrancado por el usuario sobre PROJECT KMV 1.0.0 respondió sin errores: 8 `already_stable`, 6 `child_inherited`, Obs y catálogo sin pendientes (PEN-48 comprobada en vivo).
- Consulta (2026-11-13 10:13): quitar las columnas de Records de la maestra; dependencias y orden registrados en PEN-49.

## 2026-11-13 10:20 -05:00 Prueba real de la hoja hija de Records (PEN-49)

Estado: correcta; Records en uso en Pruebas.
Evidencia (sólo lectura): 9 filas marcadas, 9 filas en `Records Requests` enlazadas por `Master Row`, sin duplicados; contexto igual a la maestra en las 9; el usuario llenó datos de Records en 4 filas de la hoja hija; procesador sin errores.

## 2026-11-13 10:26 -05:00 Migración de datos de Records a la hoja hija (PEN-49)

Estado: hecha; falta la confirmación del usuario para borrar las 14 columnas de Records de la maestra.
Evidencia: 4 filas (KMV-CC-26-001 hija, KMV-CC-26-002 madre y 2 hijas) marcadas por API; el procesador creó sus 4 filas en `Records Requests` en menos de un minuto con los datos iguales (`Designer2`, `LT Records`, `Records Status`, `Record Box`); la hoja hija tiene 13 filas.

## 2026-11-13 10:48 -05:00 Columnas de Records y de numeración provisional borradas (PEN-49, PEN-45)

Estado: hecho; `Designer2` y `Email Designer2` se quedan por ahora; el usuario revisará las 4 sin uso restantes.
Evidencia: 14 columnas borradas por API en PROJECT KMV 1.0.0 (Pruebas); 122 columnas; automatizaciones activas sin cambios; IDs y fórmulas sin errores; un `assign_failed` pasajero (hoja cambiada durante la lectura) y el ciclo siguiente correcto.

## 2026-11-13 10:55 -05:00 Revisión de facturación antes de diseñar su hoja hija (PEN-49)

Estado: revisión entregada; sin cambios en Smartsheet.
Evidencia (sólo GET): columnas, fórmulas y automatizaciones de PROJECT KMV 1.0.0 y de los originales CC y BS 2026; formato condicional aplicado por fila y paleta de `/serverinfo`; columnas del reporte Invoices. Detalle en PEN-49.

## 2026-11-13 11:36 -05:00 Facturación en los originales: fórmulas, colores y estado (PEN-49)

Estado: análisis entregado; sin cambios; el usuario revisará las columnas.
Evidencia (sólo GET, todas las filas de CC y BS 2026, sólo conteos y fórmulas normalizadas): fórmula de celda de `Invoice # Days`; formato condicional por fila deducido del formato aplicado; cruce de estado y etapa de facturación. Detalle en PEN-49.
