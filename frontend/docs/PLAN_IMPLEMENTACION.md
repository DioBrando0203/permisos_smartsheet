# Plan de implementación del frontend (PEN-06)

Orden para construir el frontend sobre el backend ya implementado. Cada fase termina con la definición de terminado de `GUIA_IA.md`, su entrada en la bitácora y un commit. Las specs de la fase pasan de "borrador" a "aprobada" antes de programarla y a "implementada" al cerrarla.

Estado: listo para empezar por F0 (2026-10-16).

## F0 Preparación (backend y esqueleto)

Backend (pequeñas, cada una con prueba):
- F0-B1: servir `frontend/dist` si existe: `/assets` como estáticos y cualquier ruta que no sea `/api`, `/docs`, `/openapi.json` ni `/assets` devuelve `index.html` (ADR-04, ADR-07). Prueba: ruta `/hojas/123` responde el `index.html`; `/api/health` sigue igual.
- F0-B2: `run.py` escribe el puerto elegido en `backend/.port` y lo borra al salir; `.port` en `.gitignore` (ADR-07).
- F0-B3: `backend/tests/fake_smartsheet.py`: FastAPI que imita los endpoints de Smartsheet que usa el cliente, con datos sintéticos de `tests/factories.py`, y registra las escrituras recibidas (ADR-10).
- F0-B4: `/api/review` aparece con dos etiquetas en Swagger (personas y auditoría): dejarle sólo "auditoría y comparación".

Frontend:
- F0-F1: proyecto Vite + React + TS con las versiones exactas de `tecnologias/STACK.md`; `vite.config.ts` de STACK; `tsconfig`, ESLint, Prettier y `src/test/setup.ts` copiados de la referencia.
- F0-F2: `tokens.css` copiado de `extractor_metadata` y recortado a lo que usa este panel, más los tokens nuevos de `estilos/SISTEMA_VISUAL.md` (severidad, barras, densidad de tabla); `base.css` y `global.css`.
- F0-F3: `components/ui` base reutilizando los de la referencia (Button, SearchBox, Avatar, StatusAlert, EmptyState, Spinner, Tabs) y nuevos (Badge, Skeleton, Toast, Dialog, ConfirmDialog, DataTable, StatTile, MeterBar, LoadingNotice, CopyText).
- F0-F4: `lib/api.ts` con `ApiError` (K-03 a K-05), `lib/errorMessages.ts` con la tabla de `contrato/CONTRATO.md`, `lib/query/` (cliente, claves, invalidación), `lib/accessLevels.ts`, `lib/severity.ts`, `lib/search.ts`, `lib/formatters.ts`, `lib/routes.ts`.
- F0-F5: MSW configurado con handlers vacíos y un fixture de `health`.

Terminado cuando: `npm run build`, `lint`, `test` y `format:check` pasan; con el backend levantado, `npm run dev` muestra la pantalla vacía con la cuenta de `/api/me` y el banner de solo lectura.

## F1 Estructura, hojas y permisos (lectura)

- Specs: SPEC-01, SPEC-02, SPEC-03 (sección Ver), cabecera de SPEC-05.
- Incluye: AppLayout con los cinco destinos (los no construidos muestran "Próximamente"), lista de hojas con alcance y búsqueda, detalle con pestaña Permisos, bloqueos explicados, exportar CSV.
- Terminado cuando: CA de esas specs con prueba; revisión visual a 320, 1024 y 1440 px con datos reales (114 hojas).

## F2 Personas

- Spec: SPEC-04 (lectura y simulación de "Quitar de varias hojas").
- Terminado cuando: CA con prueba; el directorio real (49 entradas) se ve con filtros y última conexión.

## F3 Pestañas de la hoja

- Spec: SPEC-05 (Auditoría, Actividad, Automatizaciones) y SPEC-09 (Calidad de datos de una hoja).
- Terminado cuando: CA con prueba; el plan 2026 de Crown Castle muestra sus alertas, actividad con el aviso de cuenta dominante, sus 2 automatizaciones apagadas y los Record ID repetidos.

## F4 Vistas de toda la cuenta

- Specs: SPEC-06 (Revisión), SPEC-07 (Comparar y copiar en simulación), SPEC-08 (Diseñadores), SPEC-09 (referencias de la cuenta).
- Terminado cuando: CA con prueba; las cargas largas (14 a 17 s) muestran progreso (UX-29) y no bloquean el resto del panel.

## F5 Escrituras

- Requiere: PEN-07 (verificación de escrituras reales en una hoja de prueba) y la decisión del usuario de poner `APP_READ_ONLY=false`.
- Specs: SPEC-03 (dar, cambiar, quitar), SPEC-04 y SPEC-07 (ejecutar).
- Mientras tanto la interfaz de escritura ya existe desde F1 a F4, deshabilitada por ADR-08; F5 sólo la habilita y prueba contra el Smartsheet falso (E2E) y luego contra la hoja de prueba (manual).

## F6 Cierre

- E2E de los flujos principales y pruebas visuales `@visual` en los anchos de C-09.
- Revisión de accesibilidad (teclado, foco, contraste) de todas las vistas.
- Actualizar `README.md` de la raíz y `LEVANTAMIENTO.md` con `npm run build` y el uso diario.
