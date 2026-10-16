# Guía breve para retomar el proyecto

## ¿Qué podemos continuar?

Si el usuario pregunta qué sigue, qué falta o qué podemos continuar: leer `backend/docs/REQUERIMIENTOS.md`, sección "Pendientes" (IDs PEN-xx), y responder con esa lista en orden de prioridad, con su estado y qué haría falta. No inventar pendientes fuera de esa lista; si aparece uno nuevo, agregarlo allí con su ID antes de trabajarlo. Al terminar uno, actualizar su estado y la bitácora.

Estado (2026-10-16): backend implementado y probado con la cuenta real en modo solo lectura (28 endpoints, specs SPEC-B01 a B12). Documentación del frontend lista; siguiente paso: frontend por fases empezando por F0 (`frontend/docs/PLAN_IMPLEMENTACION.md`), que incluye cuatro tareas pequeñas del backend.

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
- Modo solo lectura (`APP_READ_ONLY=true`) activo por decisión del usuario: no desactivarlo ni escribir en Smartsheet sin que lo pida (ADR-B11).
- Acceso por defecto sólo desde este equipo (loopback); el acceso desde la red es opcional y explícito por variables de entorno.

## Arquitectura y reglas

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
No escribir código con escapes (`\n`, `\d`, `\u…`) desde heredocs de shell: usar el editor o un archivo de script.
