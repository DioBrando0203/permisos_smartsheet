# Guía breve para retomar el proyecto

## ¿Qué podemos continuar?

Si el usuario pregunta qué sigue, qué falta o qué podemos continuar: leer `backend/docs/REQUERIMIENTOS.md`, sección "Pendientes" (IDs PEN-xx), y responder con esa lista en orden de prioridad, con su estado y qué haría falta. No inventar pendientes fuera de esa lista; si aparece uno nuevo, agregarlo allí con su ID antes de trabajarlo. Al terminar uno, actualizar su estado y la bitácora.

Estado (2026-11-13 19:02): backend y frontend en uso. Hoja maestra: PROJECT KMV 1.0.0 (`IDS_MASTER_SHEET_ID=8346710503018372`, PEN-48), 103 columnas (unas 4 854 filas por año; el usuario prevé 1 o 2 más para un estado por equipo, PEN-43): leer `backend/docs/HOJA_PROJECT_KMV.md` antes de tocarla y decir siempre cuántas columnas quedan. Hojas hijas en uso en Pruebas con el mecanismo común `services/childsheets/`: `Records Requests` (SPEC-B18, se activa con `Records Needed` o `Records Owner`) y `Billing` (SPEC-B19, `Invoice Status` vuelve a la maestra; desde el 2026-11-13 23:06 el metraje se llena en `Billing` y `Designers` se copia allí para la vista de diseño sobre un reporte: falta reiniciar el backend y borrar el metraje de la maestra, de 103 a 98 columnas). PEN-50 hecha: tres columnas de asignación de contacto (`Designers`, `Permitting Team`, `Records Owner`), sin columnas `Email`; avisos rehechos por el usuario (falta que el de Records se dispare sólo al cambiar `Records Owner`). `Primary` es la fórmula `="KMV-P"`; `Control Linked Tracking` también marca permisos sin proyecto y proyectos indentados como hijas. ID Manager (PEN-24, SPEC-ID01 ID-44 a ID-51): el Tracking Project sigue al cliente, `Pending ID` al instante, el procesador y su PostgreSQL sólo en el equipo Linux (B-16) y el usuario enciende el backend; `Linked Tracking` sólo enlaza proyectos anteriores; ID-51 (permiso suelto bajo su proyecto) está inactiva hasta que exista una columna `Parent Project` (decisión pendiente). Nada técnico se escribe en la hoja. Pendientes principales: cierre del paso a la 1.0.0 (PEN-48: Dynamic Views, listas de contactos, avisos y reportes), estado del proyecto en la madre (PEN-53), estados por equipo (PEN-43), clasificación de estados (PEN-27), vista de clientes con otra cuenta (PEN-44); propuestas PEN-51 (revisiones) y PEN-52 (MOT y paquetes, no recomendada). Frontend por fases en `frontend/docs/PLAN_IMPLEMENTACION.md`.

Antes de modificar, leer este archivo y la guía del lado afectado (metodología SDD: spec, plan, código, prueba, registro):
- Backend: `backend/docs/README.md` y `backend/docs/GUIA_IA.md`; reglas `PY-xx`, `SM-xx` y `patrones/PATRONES.md`.
- Frontend: `frontend/docs/README.md`, `frontend/docs/GUIA_IA.md`, `frontend/docs/PLAN_IMPLEMENTACION.md` y `frontend/docs/contrato/CONTRATO.md`; reglas `P-xx`, `E-xx`, `UX-xx`, `C-xx` y `patrones/PATRONES.md`.

## Requisitos permanentes

- Panel interno para administrar permisos (shares) de hojas de Smartsheet de una cuenta.
- Principio de producto (ADR-B15): no reemplazamos ninguna herramienta (Smartsheet, Jira, Salesforce). Sólo hacemos lo que Smartsheet no tiene, o lo que ya tiene pero mejor, sin entorpecer cómo trabaja hoy la gente: nada obliga a cambiar de herramienta ni de hábito, y Smartsheet sigue siendo la fuente de verdad.
- Smartsheet es la única fuente de verdad. Sin base de datos propia; sólo caché en memoria con vencimiento corto.
- El token vive sólo en `backend/.env` (`SMARTSHEET_ACCESS_TOKEN`). Nunca llega al navegador, a logs, a respuestas, a docs ni a pruebas.
- El token es de un administrador de la cuenta: cada escritura es real e inmediata. Nunca se cambia el propietario ni se tocan permisos heredados del workspace desde una hoja (ADR-B04, ADR-B05).
- Las pruebas automáticas no llaman a Smartsheet: usan respuestas simuladas. Las escrituras reales sólo se verifican a mano en una hoja de prueba acordada con el usuario.
- Puertos propios: backend 8710, frontend 5710 (no usar 8000 ni 5173, los usan otros proyectos del usuario). Arranque sólo desde `backend`: activar `.venv` y `python run.py`; si el 8710 está ocupado elige uno libre al azar y lo informa (ADR-B14).
- Modo solo lectura (`APP_READ_ONLY=true`) activo por decisión del usuario: no desactivarlo ni escribir en Smartsheet sin que lo pida (ADR-B11). Excepción vigente desde 2026-11-04 por decisión del usuario: `APP_READ_ONLY=false` y barreras del ID Manager activas para que el procesador asigne Stable IDs en Pruebas (SPEC-ID01 ID-36); el panel no se usa para cambiar permisos mientras tanto y se revisará al final. No revertirlo sin que lo pida.
- Alcance de cambios en Smartsheet: sólo recursos dentro del workspace `Pruebas` (ID `7965022790936452`); los demás workspaces son exclusivamente de lectura. En particular, prohibido modificar los reportes `... - Generator` de facturación y las hojas de facturación de producción (decisión expresa del usuario, 2026-11-13): sólo leerlos. Toda escritura sigue sujeta al modo solo lectura y a una autorización expresa y hoja de prueba acordada; el futuro servicio debe verificar el workspace y la hoja antes de escribir.
- Acceso por defecto sólo desde este equipo (loopback); el acceso desde la red es opcional y explícito por variables de entorno.
- Todo lo que se cree o escriba en Smartsheet (columnas, filtros, vistas, reportes, automatizaciones, mensajes) va en inglés; la conversación y los docs del repo siguen en español.
- Nada técnico a la vista en Smartsheet: el servicio no deja notas, auditoría ni texto técnico en celdas o comentarios; el rastro va a PostgreSQL y al log.

## Arquitectura y reglas

Prioridad actual: avanzar incrementalmente en ID Manager (primero simulación y después integración segura), luego catálogos y validaciones; reutilizar lo implementado y no modificar funcionalidades existentes sin necesidad. Smartsheet sigue siendo la interfaz y fuente de datos operativos; PostgreSQL conserva IDs y estado técnico. Reportes, dashboards, bitácora operativa y facturación no son el foco actual.

`backend/`: FastAPI, rutas delgadas, cliente de Smartsheet aislado en `services/smartsheet/`, reglas de permisos puras en `services/permissions/`.
`frontend/`: React/TS/Vite, Fluent 2 (tokens e iconos MIT), features autónomas y UI reutilizable fuera del dominio.
Código limpio en ambos lados: un módulo, una responsabilidad; archivos cortos (Python ≤ 300, TS ≤ 200, CSS ≤ 250 líneas); funciones cortas; reutilizar antes de crear; patrones documentados antes que soluciones ad hoc.
Mantener docs de arquitectura, specs, ADR, reglas, bloqueos, calidad y bitácora sincronizadas con el código.
Docs escritos para IA: listas e IDs citables, sin tablas ni separadores.
Bitácora: fecha/hora de America/Lima, tarea, estado y evidencia. No inventar ejecución de pruebas.
No registrar correos ni nombres reales de personas en docs, bitácora ni fixtures; usar datos sintéticos (`persona1@example.com`).

## Verificación

Backend (desde backend): `.venv/bin/python -m pytest`, `.venv/bin/python -m ruff check app tests`, `ruff format --check app tests`.
Frontend (desde frontend, cuando exista): `npm run format:check`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`.
Un servidor ya iniciado sin `--reload` no carga cambios: reiniciarlo antes de probar el flujo HTTP.
Al terminar cada tarea: commit en la rama actual con los archivos tocados (nunca `backend/.env`); el push lo hace el usuario.
No escribir código con escapes (`\n`, `\d`, `\u…`) desde heredocs de shell: usar el editor o un archivo de script.
