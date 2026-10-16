# SPEC-03 Permisos de una hoja

Estado: borrador (Ver en F1; escrituras construidas en F1 y habilitadas en F5)
Responsable del código: `features/shares/`
Relacionadas: backend SPEC-B02, B-05, B-07; ADR-03, ADR-08; UX-05 a UX-15, UX-25 a UX-28, UX-32, UX-33

## Objetivo

Ver quién tiene la hoja compartida y dar, cambiar o quitar ese acceso sin errores graves.

## Comportamiento

### Ver (pestaña Permisos, por defecto)

1. `GET /api/sheets/{id}/shares` (`ShareList`). Título de la tabla: "Personas con la hoja compartida" (no "quién la ve": Dynamic View no aparece, UX-32).
2. Columnas: Persona (avatar, nombre, correo; sin nombre, el correo), Nivel (insignia con icono), Origen ("Propio" o "Heredado del workspace") y Acciones.
3. Clave de fila: `id + scope` (B-05: el mismo `id` llega en el propio y el heredado). Una persona con ambos aparece una vez con el nivel efectivo y los dos orígenes (UX-27; `lib/groupShares.ts`).
4. Orden UX-22; la cuenta del panel marcada "(usted)" (UX-26).
5. Filtro por nombre o correo cuando hay más de 10 personas.

### Cambiar nivel

1. Fila editable (`editable: true`): `AccessLevelSelect` sin "Propietario".
2. Subir: guarda al instante, salvo a Administrador (UX-07). Bajar: `ConfirmDialog` (UX-06).
3. Mientras guarda: spinner y fila deshabilitada; al confirmar, Toast (UX-09).

### Quitar acceso

1. Botón "Quitar" con `aria-label="Quitar acceso a {nombre}"`.
2. `RemoveShareDialog` con persona, hoja y nivel; botón `danger` "Quitar acceso". Si es la cuenta del panel, confirmación reforzada (UX-26).

### Dar acceso

1. "Compartir" (único `primary` de la vista) abre `ShareDialog`.
2. Destinatarios en chips; autocompletado con el directorio (`/api/users`, que ya incluye contactos) y grupos (`/api/groups`); pegar varios correos (UX-13).
3. Nivel por defecto Editor; sin Propietario. "Avisar por correo" desmarcado; al marcarlo, asunto y mensaje (UX-10).
4. Botón "Dar acceso a N personas" (UX-14). Resultado con creados y omitidos (UX-11); con error, el diálogo queda abierto con StatusAlert.

### Bloqueos (siempre visibles, UX-08)

- `locked_reason`: `OWNER` "Propietario de la hoja"; `INHERITED` "Heredado del workspace: cámbielo en el workspace"; `NO_PERMISSION` "La cuenta del panel no puede administrar esta hoja".
- Hoja de otra persona (`in_my_list: false`): sin "Compartir"; aviso "Sólo consulta: la hoja es de {dueño} y no está compartida con la cuenta del panel" (UX-33).
- Modo solo lectura: "Compartir", selectores y "Quitar" deshabilitados con el motivo del banner (UX-28).

## Estados

- Carga: 6 filas esqueleto.
- Vacío: "Sólo la cuenta del panel tiene esta hoja compartida" con "Compartir".
- Éxito: tabla.
- Parcial: no aplica.
- Error: StatusAlert con texto por código, `ref_id` y "Reintentar"; errores de escritura junto a la fila o en el diálogo.

## Criterios de aceptación

- CA-01: un permiso propio y uno heredado con el mismo `id` se muestran como una persona con dos orígenes, sin advertencias de clave repetida de React. Prueba: `groupShares.test.ts` y componente.
- CA-02: bajar de Editor a Visor pide confirmación y no llama al backend si se cancela. Prueba: componente con MSW.
- CA-03: el nivel no cambia en pantalla hasta la respuesta del backend. Prueba: componente con MSW y respuesta demorada.
- CA-04: propietario, heredados y hojas de otra persona no tienen controles activos y muestran el motivo. Prueba: componente.
- CA-05: con `read_only: true` ningún control de escritura está activo. Prueba: componente con MSW.
- CA-06: pegar "a@example.com; b@example.com, a@example.com" crea dos chips y avisa del duplicado. Prueba: `recipients.test.ts`.
- CA-07: "Avisar por correo" envía `send_email=true` sólo si se marca. Prueba: componente con MSW.
- CA-08: resultado con omitidos muestra el texto de UX-11. Prueba: componente.
- CA-09: dar, cambiar y quitar contra el backend con el Smartsheet falso; el falso recibe exactamente las escrituras esperadas. Prueba: e2e (F5).

## Accesibilidad

`<table>` con `<caption>` "Personas con la hoja compartida: {hoja}"; selector con `aria-label="Nivel de acceso de {nombre}"`; Toast con `role="status"`; diálogos con `aria-labelledby`.

## Responsive

640 o menos: tarjetas por persona en lugar de tabla.
