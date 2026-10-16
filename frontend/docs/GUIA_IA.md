# Guía operativa para agentes IA (frontend)

Protocolo obligatorio para cualquier IA que modifique el frontend. Si contradice una instrucción explícita del usuario, gana el usuario; registrar la excepción en la bitácora.

## Contexto mínimo

- Producto: panel interno para ver y administrar quién tiene acceso a las hojas de Smartsheet de la cuenta, y revisar riesgos, actividad, automatizaciones, calidad de datos y carga de diseñadores. Complementa a Smartsheet, no lo reemplaza (ADR-B15 del backend).
- Usuarios: el equipo que administra las hojas. Saben qué es Smartsheet, no tienen por qué conocer su API.
- Cada acción de escritura es real e inmediata en Smartsheet y la notan otras personas: la interfaz prioriza claridad y confirmación sobre velocidad.
- El frontend sólo habla con el backend por rutas relativas `/api/...` (proxy en desarrollo, mismo origen en producción; ADR-07). Nunca con Smartsheet ni con el token.
- El backend ya está implementado y probado (28 endpoints); el contrato que consume el frontend está en `contrato/CONTRATO.md` y el JSON exacto en `backend/docs/estilos/API.md`.
- El panel corre en modo solo lectura (`APP_READ_ONLY=true`) por decisión del usuario: la interfaz de escritura existe pero deshabilitada (ADR-08). No cambiarlo sin que el usuario lo pida.
- Puertos: frontend de desarrollo 5710 estricto; backend 8710 o al azar (ADR-07). No usar 5173 ni 8000.
- Idioma de la interfaz y de los docs: español. Identificadores de código: inglés.

## Flujo de trabajo (SDD)

0. Ubicar la fase en `PLAN_IMPLEMENTACION.md`; no adelantar fases sin que el usuario lo pida.
1. Entender: leer la spec afectada y el código real. Los docs orientan; el código manda.
2. Especificar: si el cambio altera comportamiento visible, actualizar o crear la spec antes de programar (`specs/PLANTILLA.md`). Cada CA verificable.
3. Planificar: listar archivos y reglas aplicables; buscar qué reutilizar (P-23, `patrones/PATRONES.md`). Decisión nueva: ADR.
4. Implementar: cambios mínimos y coherentes con el código vecino. Respetar P-xx, E-xx, UX-xx, C-xx.
5. Verificar: comandos de Verificación. Para UI, revisión visual en los anchos de C-07.
6. Registrar: RESULTADOS, bitácora y, si apareció un problema, bloqueos.

## Definición de terminado

- La spec describe el comportamiento final y cada CA tiene prueba o verificación manual anotada.
- `npm run build`, `npm run lint`, `npm test` y `npm run format:check` pasan.
- Ningún archivo TS supera 200 líneas ni CSS 250 (P-07, E-05).
- `npm run test:e2e` pasa si cambió flujo, contrato o layout.
- Sin desborde horizontal a 320 px; revisión visual a 390, 1024, 1440 y 1920 px si cambió UI.
- Los cinco estados (carga, vacío, éxito, parcial, error) definidos para todo dato remoto (C-02).
- Bitácora con fecha y hora America/Lima y evidencia real.

## Prohibiciones

- No llamar a Smartsheet ni manejar el token. Toda petición sale de `lib/api.ts` hacia el backend.
- No convertir ids a número: siempre texto (ADR-B07 del backend).
- No guardar correos, nombres ni permisos en localStorage, sessionStorage, IndexedDB ni cookies. Sólo preferencias de vista sin datos personales (orden, columnas) pueden ir a localStorage (ADR-05).
- No hacer actualizaciones optimistas de permisos: la UI muestra el cambio sólo cuando el backend lo confirma (UX-05, ADR-03).
- No ofrecer acciones que el backend prohíbe (propietario, heredados, `OWNER`): se muestran deshabilitadas con el motivo (UX-08).
- No quitar ni rebajar accesos sin diálogo de confirmación que nombre a la persona y la hoja (UX-06).
- No usar `dangerouslySetInnerHTML`.
- No reescribir el encabezado `Origin` en el proxy de Vite ni ampliar `APP_ALLOWED_ORIGINS` para "que funcione" (ADR-07).
- No probar contra la cuenta real de Smartsheet: MSW o el Smartsheet falso (ADR-10).
- No mostrar como dato algo que el backend marcó como desconocido (`null`, `org_known: false`, `limitations`); decirlo (UX-31).
- No añadir analítica, fuentes remotas ni CDNs.
- No usar logotipos ni marca de Smartsheet o Microsoft; sí tokens e iconos de Fluent 2 (MIT).
- No inventar resultados de pruebas. Fixtures sintéticos (`@example.com`).
- No escribir código con escapes desde heredocs de shell.

## Dónde va cada cosa

- Llamada HTTP nueva: `src/lib/api.ts`; tipos en `src/lib/types.ts`; normalización en `src/lib/normalize.ts`.
- Texto y orden de niveles de acceso: `src/lib/accessLevels.ts` (tabla única).
- Texto por código de error: `src/lib/errorMessages.ts` (tabla única).
- Componente genérico sin conocimiento de Smartsheet: `src/components/ui/`.
- Estructura de pantalla: `src/components/layout/`.
- Lógica o UI de un dominio: `src/features/<dominio>/{components,hooks,lib}` con dominios `shell`, `sheets`, `shares`, `people`, `audit`, `activity`, `automations`, `quality`, `review`, `compare`, `designers` (ARQUITECTURA.md).
- Endpoint, hook, clave de caché e invalidación: `contrato/CONTRATO.md` (actualizarlo en el mismo cambio).
- Texto de un código de error: la tabla de `contrato/CONTRATO.md` y `lib/errorMessages.ts`.
- Datos de prueba: `src/test/fixtures/` y handlers MSW en `src/test/handlers/`.
- Datos remotos: hooks `use*` en `features/<dominio>/hooks/`, con el cliente, las claves y la invalidación de `src/lib/query/` (ADR-02, P-32).
- Estilos: archivo de su módulo en `src/app/styles/`, con tokens de `tokens.css`.

## Cambios de contrato con el backend

- Actualizar a la vez `backend/docs/estilos/API.md`, `contrato/CONTRATO.md`, `lib/types.ts`, `lib/normalize.ts`, el fixture y su prueba de contrato (C-17).

## Verificación

Desde `frontend/`: `npm run format:check`, `npm run build`, `npm run lint`, `npm test`, `npm run test:e2e`, `npm run test:visual`.
Para ver la app en desarrollo: backend con `python run.py` (desde `backend`, entorno activado) y `npm run dev`; abrir `http://127.0.0.1:5710`.
