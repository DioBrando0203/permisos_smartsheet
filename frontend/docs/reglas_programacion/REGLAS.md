# Reglas de programación (TypeScript y React)

Obligatorias salvo que digan "preferir". Citar el ID en revisiones y en la bitácora.

## Tipado y estructura

- P-01: TypeScript estricto. Prohibido `any`, `as unknown as` y `!` sobre datos del backend.
- P-02: toda llamada HTTP vive en `lib/api.ts`. Los componentes reciben datos normalizados (`lib/types.ts`), nunca `Response` ni JSON crudo.
- P-03: una feature no importa la `lib`, hooks ni estado de otra feature. Excepción vigente: ADR-06.
- P-04: `components/ui` y `components/layout` no conocen hojas, permisos ni la API.
- P-05: nunca `dangerouslySetInnerHTML` ni `innerHTML`.
- P-06: lógica pura (validación de correos, agrupación, orden, búsqueda) en funciones sin React en `lib/` o `features/<dominio>/lib/`, con pruebas unitarias.
- P-07: un componente por responsabilidad. Máximo 200 líneas por archivo; al pasar de 150 o al mezclar estados, separar.
- P-08: ids siempre `string` (ADR-B07 del backend).

## Estado y efectos

- P-09: datos del servidor sólo con TanStack Query desde hooks de feature; nunca `useEffect` + `fetch` en componentes (ADR-02).
- P-10: mutaciones con `useMutation`, invalidación explícita de las claves afectadas al confirmar y sin `onMutate` optimista (UX-05).
- P-11: claves de consulta definidas en `lib/query/keys.ts`, nunca arreglos literales repartidos.
- P-12: efectos sólo para sincronizar con sistemas externos; derivar datos en render.
- P-13: `key` para reiniciar estado local al cambiar de entidad (`<ShareTable key={sheetId}>`).
- P-14: estado de vista compartible (búsqueda, hoja o persona abierta) en la URL.

## Accesibilidad en código

- P-15: elementos interactivos son `<button>`, `<a>`, `<input>` o `<select>` reales. Prohibido `onClick` en `div`.
- P-16: botones sólo con icono llevan `aria-label`; iconos decorativos `aria-hidden="true"`.
- P-17: diálogos con `<dialog>` nativo y `showModal()`; foco al primer control lógico y regreso al botón que lo abrió.
- P-18: carga con `aria-busy` o `role="status"`; errores con `role="alert"`; avisos de éxito con `role="status"`.
- P-19: tablas con `<table>`, `<th scope>` y `<caption>` (puede ser visualmente oculto).

## Estilo de código

- P-20: Prettier (`printWidth` 110, sin punto y coma, comillas simples) y ESLint sin errores ni warnings.
- P-21: nombres en inglés; textos visibles y comentarios en español.
- P-22: comentar el porqué, no el qué.
- P-23: antes de crear un componente, hook o función, buscar uno existente (`rg`) y ampliarlo si encaja.
- P-24: regla de tres: la tercera copia obliga a extraer.
- P-25: componentes genéricos en `components/ui` con API mínima y nombres de Fluent (`appearance`, `size`).
- P-26: decisiones por tipo de dato en tablas (`accessLevels`, `errorMessages`, `lockedReasons`), no condicionales en JSX.
- P-27: handlers y funciones de máximo 40 líneas; cuerpo de componente de máximo 120.
- P-28: máximo 7 props de datos o callbacks por componente; con más, agrupar o dividir.
- P-29: sin estado duplicado: lo derivable se calcula en render.
- P-30: clases CSS en kebab-case `bloque__elemento--variante`; estados con `is-*` o atributos ARIA/data. Sin utilidades en JSX.

## Dependencias

- P-31: versiones exactas en `package.json`. Toda dependencia nueva se justifica en `tecnologias/STACK.md` y pasa `npm audit`.

## Datos remotos (agregadas el 2026-10-16)

- P-32: claves de consulta sólo desde `lib/query/keys.ts` y con los parámetros que cambian la respuesta (CONTRATO.md). `staleTime` 60 s por defecto; consultas lentas (diseñadores, automatizaciones de la cuenta) 5 min.
- P-33: `fetch` con `AbortController` y plazo de 120 s (las cargas más largas verificadas rondan 17 s); al vencer, `ApiError` con `code = "BACKEND_UNREACHABLE"` y texto de demora.
- P-34: una función de normalización por endpoint en `lib/normalize.ts`; los componentes nunca leen campos del JSON crudo.
- P-35: URLs internas con `lib/routes.ts` (`sheetPath(id, tab)`, `personPath(key)`), nunca armadas a mano; `key` de persona siempre con `encodeURIComponent`.
- P-36: claves de React estables y únicas: permisos con `id + scope` (B-05 del backend), personas con `key`, filas con `row_id`, pasos de simulación con `key + sheet_id`.

