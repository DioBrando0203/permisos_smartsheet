# SPEC-03 Permisos de una hoja

Estado: borrador
Responsable del código: `features/shares/`
Relacionadas: SPEC-B02 del backend, UX-05 a UX-15, UX-25 a UX-27, ADR-03

## Objetivo

Ver quién tiene acceso a una hoja y dar, cambiar o quitar ese acceso sin errores graves.

## Comportamiento

### Ver

1. Cabecera: nombre de la hoja, "Abrir en Smartsheet", número de personas con acceso, "Actualizado hace X" y botón primario "Compartir".
2. Tabla con columnas Persona (avatar, nombre, correo), Nivel, Origen ("Propio" o "Heredado del workspace") y Acciones.
3. Orden UX-22. Una persona con propio y heredado aparece una vez con el nivel efectivo y ambos orígenes (UX-27).
4. Filtro por nombre o correo encima de la tabla cuando hay más de 10 personas.

### Cambiar nivel

1. El nivel de cada fila editable es un `AccessLevelSelect`.
2. Subir: guarda al instante (salvo a Administrador, UX-07). Bajar: `ConfirmDialog` (UX-06).
3. Mientras guarda, la fila muestra spinner y queda deshabilitada; al confirmar, Toast (UX-09).

### Quitar acceso

1. Botón "Quitar" (icono de persona con menos, `aria-label="Quitar acceso a {nombre}"`).
2. `RemoveShareDialog` con nombre, hoja y nivel actual; botón `danger` "Quitar acceso".
3. Si es la cuenta del token, confirmación reforzada (UX-26).

### Dar acceso

1. "Compartir" abre `ShareDialog`.
2. Destinatarios: chips; autocompletado con personas ya conocidas (`/api/users`) y grupos (`/api/groups`); pegar varios correos (UX-13).
3. Nivel: por defecto Editor; lista sin Propietario.
4. "Avisar por correo" desmarcado; al marcarlo, asunto y mensaje opcionales.
5. Botón "Dar acceso a N personas" (UX-14).
6. Resultado: Toast con creados y omitidos (UX-11); el diálogo se cierra sólo si todo se creó o se omitió; si hubo error, queda abierto con StatusAlert.

### Bloqueos

- Propietario, heredado y hoja sin permiso de administración: selector y Quitar deshabilitados con `LockedHint` (UX-08).
- Hoja "Sólo lectura": no se muestra "Compartir"; un aviso explica por qué.

## Estados

- Carga: 6 filas esqueleto.
- Vacío: "Sólo usted tiene acceso a esta hoja" con "Compartir".
- Éxito: tabla.
- Parcial: no aplica a la lectura de una hoja.
- Error: StatusAlert con texto por código, `ref_id` y "Reintentar". Errores de escritura junto a la fila o en el diálogo.

## Criterios de aceptación

- CA-01: bajar de Editor a Visor pide confirmación y no llama al backend si se cancela. Prueba: componente con MSW.
- CA-02: el nivel no cambia en pantalla hasta que el backend responde. Prueba: componente con MSW y respuesta demorada.
- CA-03: propietario y heredados no tienen controles activos y muestran el motivo. Prueba: componente.
- CA-04: pegar "a@example.com; b@example.com, a@example.com" crea dos chips y avisa del duplicado. Prueba: `recipients.test.ts`.
- CA-05: "Avisar por correo" envía `send_email=true` sólo si se marca. Prueba: componente con MSW.
- CA-06: resultado con omitidos muestra el texto de UX-11. Prueba: componente.
- CA-07: Esc con datos escritos pide confirmar el descarte. Prueba: componente.
- CA-08: flujo completo dar, cambiar y quitar contra el backend con Smartsheet simulado. Prueba: e2e.

## Accesibilidad

Tabla con `<caption>` "Personas con acceso a {hoja}"; selector con `aria-label="Nivel de acceso de {nombre}"`; Toast en `role="status"`; diálogos con título como `aria-labelledby`.

## Responsive

640 o menos: tarjetas por persona en lugar de tabla (SISTEMA_VISUAL).
