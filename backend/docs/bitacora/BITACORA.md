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
