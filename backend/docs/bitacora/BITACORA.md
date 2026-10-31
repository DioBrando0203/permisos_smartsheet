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
