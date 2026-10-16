# Patrones de diseño (frontend)

Catálogo de patrones de código y de UI/UX a usar. Antes de crear una estructura nueva, reutilizar una de estas.

## Patrones de UI/UX

### Maestro-detalle

Dónde: `/hojas` (lista de hojas y permisos de la seleccionada) y `/personas` (lista de personas y sus hojas).
Qué: lista a la izquierda, detalle a la derecha; en pantallas de 860 px o menos, la lista ocupa todo y el detalle se abre encima con botón Volver.
Cuándo: recorrer muchos elementos y revisar uno a la vez.

### Tabla de datos con acciones por fila

Dónde: `ShareTable`, `PersonDetail`.
Qué: columnas Persona, Nivel, Origen y Acciones; el nivel se cambia en la propia fila con `AccessLevelSelect`; "Quitar" es un botón sutil con icono al final.
Reglas: cabecera fija, orden UX-22, acciones visibles siempre (no sólo al pasar el ratón), estado de carga por fila (UX-05).
Evitar: menús de "..." para la acción principal de la fila.

### Edición en línea con confirmación selectiva

Dónde: `AccessLevelSelect` dentro de `ShareRow`.
Qué: elegir un nivel más alto guarda al instante; elegir uno más bajo abre `ConfirmDialog` (UX-06, UX-07). Mientras guarda, el selector queda deshabilitado con spinner.

### Diálogo de compartir

Dónde: `ShareDialog`.
Qué: un diálogo modal con: destinatarios (chips con autocompletado de personas y grupos conocidos), nivel (con descripciones), casilla "Avisar por correo" y mensaje opcional. Botón primario con el número de personas (UX-14).
Referencia: el diálogo "Compartir" de Smartsheet y de Microsoft 365, para que resulte familiar.

### Confirmación destructiva

Dónde: `ConfirmDialog` (ui) usado por `RemoveShareDialog`.
Qué: título con la acción ("¿Quitar acceso a Ana Pérez?"), texto con consecuencia ("Dejará de ver Plan 2026. Puede volver a darle acceso después."), botones "Cancelar" (foco inicial) y acción en `danger`.
Variante reforzada: quitarse a sí mismo exige escribir el nombre de la hoja (UX-26).

### Bloqueo explicado

Dónde: `LockedHint`.
Qué: control deshabilitado + icono de candado + texto corto + tooltip con la explicación completa, desde la tabla `lockedReasons` (UX-08).

### Aviso de resultado (Toast)

Dónde: `Toast` (ui), disparado por las mutaciones.
Qué: aviso breve abajo a la derecha (arriba en móvil) con el resultado en una frase; errores no usan Toast sino `StatusAlert` junto a la acción, porque requieren lectura (UX-18).

### Esqueletos de carga

Dónde: `Skeleton` en listas y tablas.
Qué: filas grises con la forma del contenido final; nunca pantalla en blanco (UX-16).

### Estado vacío con siguiente paso

Dónde: `EmptyState` (ui).
Qué: icono, frase que explica, y un botón con la siguiente acción (UX-17).

### Frescura de datos

Dónde: `SheetHeader`, cabecera de `PeopleList`.
Qué: "Actualizado hace X" y botón Actualizar (UX-20).

### Pestañas con carga diferida

Dónde: `SheetTabs` (Permisos, Auditoría, Actividad, Automatizaciones, Calidad).
Qué: la pestaña inicial es Permisos; cada otra pestaña monta su panel (y su consulta) sólo al abrirse; la elegida queda en `?tab=` (ADR-11).

### Resumen con detalle (drill-down)

Dónde: Revisión, Auditoría, Diseñadores.
Qué: StatTiles arriba con las cifras; debajo, tablas cuyas filas enlazan a la persona, la hoja o la pestaña que explica la cifra (UX-34).

### Simular y luego aplicar

Dónde: Comparar (copiar permisos), Personas (quitar de varias hojas).
Qué: "Ver qué pasaría" → tabla de pasos con conteos → "Aplicar N cambios" con confirmación → resultado por paso (UX-30). La simulación es una consulta más; la aplicación es una mutación pesimista.

### Consulta larga con aviso

Dónde: directorio, revisión, automatizaciones de la cuenta, diseñadores, historial de fila.
Qué: `LoadingNotice` a los 3 s con qué se lee y cuánto suele tardar; la consulta sigue aunque se cambie de vista y su resultado queda en caché (UX-29).

### Banner de estado global

Dónde: `features/shell/ReadOnlyBanner`, avisos de backend caído o token.
Qué: el estado del panel (solo lectura, sin conexión) se muestra una vez arriba y cada control de escritura lee `useHealth().readOnly` para deshabilitarse con el motivo (ADR-08).

## Patrones de código

### Layout con huecos (slots)

Dónde: `AppLayout` (`nav`, `list`, `detail`, `toolbar`).
Qué: el layout no conoce el dominio; las rutas le pasan los paneles.

### Contenedor y presentación

Dónde: hooks de feature y componentes de ruta frente a `ShareRow`, `SheetRow` (props a JSX).
Regla: un componente de presentación no llama a la API ni a TanStack Query.

### Consultas y mutaciones (TanStack Query)

Dónde: `features/*/hooks`, claves en `lib/query/keys.ts`.
Qué: caché, reintento, cancelación y estados de carga declarativos; las mutaciones invalidan al confirmar (P-10).

### Fachada de API y normalización

Dónde: `lib/api.ts`, `lib/normalize.ts`.
Qué: único punto HTTP; convierte errores en `ApiError` con `code`, `message` y `refId`; tolera campos ausentes.

### Tabla de decisión

Dónde: `lib/accessLevels.ts`, `lib/errorMessages.ts`, `features/shares/lib/lockedReasons.ts`.
Qué: un dato (nivel, código de error, motivo de bloqueo) se traduce a etiqueta, descripción, icono y acción en un mapa, no en `if` repartidos.

### Datos simulados con la forma del contrato

Dónde: `src/test/fixtures/` y `src/test/handlers/<feature>.ts`.
Qué: un fixture por respuesta del contrato con datos sintéticos (`@example.com`); los handlers MSW los devuelven y permiten variar casos (vacío, parcial, error, demora). Las pruebas de componente nunca arman JSON a mano.

### Funciones puras

Dónde: `lib/search.ts`, `features/shares/lib/groupShares.ts`, `features/shares/lib/recipients.ts`.
Qué: sin React; se prueban sin DOM.

### Estado en la URL

Dónde: rutas y `?q=`.
Qué: búsqueda y selección compartibles y navegables con Atrás (UX-23).

### Diálogo nativo

Dónde: `Dialog`, `ConfirmDialog`.
Qué: `<dialog>` con `showModal()`: foco atrapado, fondo inerte y Esc gratis.

## Antipatrones prohibidos

- Actualizar la UI antes de que el backend confirme una escritura.
- Ocultar una acción prohibida sin explicar por qué.
- Confirmar con botones "Aceptar"/"Sí" en lugar de la acción concreta.
- `useEffect` + `fetch` en componentes.
- Diálogos dentro de diálogos.
- Spinners de pantalla completa para recargas.
- Utilidades genéricas `utils.ts`.
- Color como única diferencia entre niveles o estados.
