# Guía breve para retomar el proyecto

Estado 2026-11-16 (PEN-55): el frontend, panel de permisos y GIS se trasladaron a `../gis_permisos`. Este proyecto conserva el procesador y catálogo de Smartsheet; las referencias históricas al frontend y al panel en este archivo y en las guías anteriores no describen la estructura actual. No se probaron los cambios por decisión del usuario.

## ¿Qué podemos continuar?

Si el usuario pregunta qué sigue, qué falta o qué podemos continuar: leer `backend/docs/KMV_2.0.md` (pendientes K2-80 en adelante) y `backend/docs/REQUERIMIENTOS.md`, sección "Pendientes" (IDs PEN-xx), y responder con esa lista en orden de prioridad, con su estado y qué haría falta. No inventar pendientes fuera de esa lista; si aparece uno nuevo, agregarlo allí con su ID antes de trabajarlo. Al terminar uno, actualizar su estado y la bitácora.

Estado (2026-11-16 19:14): versión vigente KMV 2.0 (prototipo en Pruebas; `backend/.env` apunta a ella). Leer `backend/docs/KMV_2.0.md` antes de tocar hojas, vistas o servicio: es el estado actual, con pendientes (K2-80 en adelante) y criterio; las vistas, en `backend/docs/VISTAS_KMV_2.0.md`. Maestra 2.0: 79 columnas (unas 6 329 filas por año): decir siempre cuántas columnas tiene tras cualquier cambio. La 1.0.0 (`backend/docs/HOJA_PROJECT_KMV.md`, 98 columnas) ya no la procesa el servicio; el historial de las dos está en REQUERIMIENTOS (PEN-48 a PEN-54). El procesador de IDs y su PostgreSQL pasan a Railway (PEN-56, `backend/docs/DESPLIEGUE_RAILWAY.md`): la base se copió y verificó allí el 2026-11-24 y el procesador del equipo Linux quedó apagado (`IDS_MONITOR_ENABLED=false`), para que nunca vuelva a numerar con su base local; nunca correr una pasada manual con el backend encendido. Nada técnico se escribe en la hoja.

Antes de modificar, leer este archivo y la guía del lado afectado (metodología SDD: spec, plan, código, prueba, registro):
- Backend: `backend/docs/README.md` y `backend/docs/GUIA_IA.md`; reglas `PY-xx`, `SM-xx` y `patrones/PATRONES.md`.
- Frontend: `frontend/docs/README.md`, `frontend/docs/GUIA_IA.md`, `frontend/docs/PLAN_IMPLEMENTACION.md` y `frontend/docs/contrato/CONTRATO.md`; reglas `P-xx`, `E-xx`, `UX-xx`, `C-xx` y `patrones/PATRONES.md`.

## Requisitos permanentes

- Panel interno para administrar permisos (shares) de hojas de Smartsheet de una cuenta.
- Principio de producto (ADR-B15): no reemplazamos ninguna herramienta (Smartsheet, Jira, Salesforce). Sólo hacemos lo que Smartsheet no tiene, o lo que ya tiene pero mejor, sin entorpecer cómo trabaja hoy la gente: nada obliga a cambiar de herramienta ni de hábito, y Smartsheet sigue siendo la fuente de verdad.
- Smartsheet es la única fuente de verdad. Sin base de datos propia; sólo caché en memoria con vencimiento corto.
- El token vive sólo en `backend/.env` (`SMARTSHEET_ACCESS_TOKEN`) y, por decisión del usuario (2026-11-24), en la variable del servicio `permisos_smartsheet` de Railway (SPEC-B22 DP-11). Nunca llega al navegador, a logs, a respuestas, a docs ni a pruebas.
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

## Mapa y herramientas

- Procesador en Railway (PEN-56): `backend/docs/DESPLIEGUE_RAILWAY.md` (estado, pasos y cambios del día a día) y SPEC-B22. Nunca dos procesadores con bases distintas: se repetirían IDs.
- Mapa de la 2.0 (hojas, vistas, reportes, automatizaciones, qué hace el servicio, flujo y diagramas): `backend/docs/mapa_2.0/`.
- Herramienta opcional de navegador (Playwright) para lo que la API de Smartsheet no permite (Dynamic Views, formato condicional, Admin Center): `herramientas/smartsheet_ui/` y `backend/docs/PLAYWRIGHT_SMARTSHEET.md`. Sólo con autorización expresa del usuario para cada tarea; el usuario inicia sesión a mano; escrituras sólo en Pruebas.
