# Reglas de UX

Obligatorias. Cómo se comporta y se lee la interfaz. Diseño visual en `reglas_estilos/` (E-xx); patrones concretos en `patrones/PATRONES.md`.

## Principios

- UX-01: la pregunta principal se responde sin clics extra: al abrir una hoja se ve de inmediato quién la tiene compartida y con qué nivel. Las demás vistas de la hoja van en pestañas, pero Permisos es siempre la pestaña inicial (ADR-11).
- UX-02: una acción principal por zona. En el detalle de una hoja, "Compartir" es el único botón `primary`; en Comparar, "Aplicar N cambios"; en las revisiones no hay `primary` (sólo consultan).
- UX-03: los niveles se nombran como en Smartsheet en español y con su descripción corta: Visor (ver), Comentarista (ver y comentar), Editor (editar filas), Editor que comparte (editar y compartir), Administrador (todo menos eliminar la hoja), Propietario. La tabla vive en `lib/accessLevels.ts`.
- UX-04: lenguaje del usuario: "Dar acceso", "Cambiar nivel", "Quitar acceso", "Heredado del workspace". Nunca "share", "scope", "ITEM" ni códigos de error en la vista principal.

## Escrituras seguras

- UX-05: sin actualizaciones optimistas. Mientras el backend responde, la fila o el botón muestran un indicador y se bloquean; el valor cambia sólo con la confirmación (ADR-03).
- UX-06: quitar acceso o bajar de nivel abre un diálogo de confirmación que nombra a la persona, la hoja, el nivel actual y el nuevo. El botón de confirmar dice la acción exacta ("Quitar acceso"), no "Aceptar". El foco inicial va a "Cancelar".
- UX-07: subir de nivel no pide confirmación, pero sí cuando el nuevo nivel es Administrador (puede compartir y cambiar todo).
- UX-08: acciones prohibidas se muestran deshabilitadas con el motivo visible (icono de candado y texto, más tooltip): "Propietario de la hoja", "Heredado del workspace: cámbielo en el workspace", "Su cuenta no puede administrar esta hoja". Nunca se ocultan sin explicar.
- UX-09: tras una escritura correcta, un aviso breve (Toast, 5 s, con `role="status"`) dice qué cambió: "Se dio acceso de Editor a 2 personas en Plan 2026". Sin botón Deshacer, porque Smartsheet no lo permite de forma segura; el aviso basta para corregir a mano.
- UX-10: dar acceso no envía correo por defecto; la casilla "Avisar por correo" está desmarcada y, al marcarla, aparece el mensaje opcional.
- UX-11: resultados parciales se explican: si de 5 destinatarios 2 ya tenían acceso, el aviso dice "Se dio acceso a 3. 2 ya tenían acceso (sin cambios)".

## Formularios

- UX-12: validar al salir del campo y al enviar, no en cada tecla. Error junto al campo, con texto que dice cómo corregirlo ("Escriba un correo válido, por ejemplo nombre@empresa.com").
- UX-13: el campo de destinatarios acepta pegar varios correos separados por coma, punto y coma, espacio o salto de línea y los convierte en chips; los duplicados se descartan con aviso.
- UX-14: el botón de enviar se habilita sólo con datos válidos y dice lo que hará con el número: "Dar acceso a 3 personas".
- UX-15: Enter envía y Esc cierra el diálogo; si hay datos escritos, Esc pide confirmar antes de descartar.

## Estados

- UX-16: carga con esqueletos que respetan la forma final (filas de tabla), no un spinner en pantalla vacía. Después de 10 s, texto "Smartsheet está tardando más de lo normal".
- UX-17: vacío con explicación y siguiente paso: "Nadie más tiene acceso a esta hoja" con botón "Compartir"; "Ninguna hoja coincide con 'xyz'" con "Borrar búsqueda".
- UX-18: error con causa en lenguaje del usuario, acción ("Reintentar") y, si existe, el código de soporte (`ref_id`) en texto pequeño copiable.
- UX-19: parcial visible: si la vista por persona no pudo leer algunas hojas, un aviso arriba dice cuántas y permite reintentar; los datos leídos se muestran igual.
- UX-20: datos de caché: cada vista muestra "Actualizado hace 2 min" y un botón "Actualizar" que fuerza `refresh=true`.

## Búsqueda, orden y navegación

- UX-21: búsqueda inmediata (sin botón), con espera de 200 ms, sin tildes ni mayúsculas, resaltando la coincidencia; el texto queda en la URL (`?q=`).
- UX-22: orden por defecto de permisos: nivel descendente, luego nombre; el propietario siempre primero. La lista de hojas por nombre.
- UX-23: cada hoja y persona tiene URL propia; Atrás del navegador vuelve al estado anterior; el detalle conserva la búsqueda de la lista.
- UX-24: enlace "Abrir en Smartsheet" en el detalle de la hoja, en pestaña nueva, con icono de enlace externo.

## Identidad de las personas

- UX-25: cada persona se muestra con avatar de iniciales, nombre y correo debajo; sin nombre, el correo ocupa el lugar del nombre. Los grupos con icono de grupo y la palabra "Grupo".
- UX-26: la cuenta del token se marca con "(usted)" para que nadie se quite el acceso a sí mismo sin darse cuenta; quitarse a sí mismo exige confirmación reforzada (escribir el nombre de la hoja).
- UX-27: una persona con acceso propio y heredado en la misma hoja aparece una vez, con el nivel efectivo (el más alto) y el detalle de ambos orígenes.

## Modo solo lectura, cargas largas y simulaciones

- UX-28: con `read_only: true` (ADR-08) toda acción que escribe está visible y deshabilitada, con el motivo "Modo solo lectura: el panel no cambia nada en Smartsheet" en el tooltip y en texto junto al botón principal de la vista. Las simulaciones siguen activas.
- UX-29: una consulta que lleva más de 3 s muestra `LoadingNotice` con qué está haciendo ("Leyendo las automatizaciones de 110 hojas…") y la duración esperada si se conoce (CONTRATO.md); a los 30 s agrega "Smartsheet está tardando más de lo normal". El resto del panel sigue usable; cambiar de vista no cancela la consulta (queda en caché).
- UX-30: toda operación que cambia muchas cosas (copiar permisos, quitar de varias hojas) es en dos pasos: "Ver qué pasaría" (simulación con conteos por acción y lista de pasos) y luego "Aplicar N cambios" con confirmación que repite los conteos. Tras aplicar, el resultado se muestra paso a paso (hecho o falló y por qué), nunca sólo "listo".
- UX-31: lo que el panel no puede saber se dice: `limitations` de la actividad, `org_known: false` en la auditoría, `has_access: null` en diseñadores ("No se pudo saber"), hojas fallidas. Nunca se rellena con un valor supuesto.

## Lenguaje según lo que Smartsheet expone

- UX-32: decir "personas con la hoja compartida", no "quién ve la hoja": quien entra sólo por Dynamic View no aparece (B-07 del backend). Una hoja con `has_dynamic_view` lleva la insignia "Vista dinámica" y la nota "Puede haber personas que la ven por una vista dinámica y no aparecen aquí".
- UX-33: una hoja de otra persona de la organización (`in_my_list: false`) se marca "De otra persona" con su dueño; sus permisos se consultan, pero no se ofrece ninguna escritura (aviso, no error).
- UX-34: cada cifra resumida (StatTile, conteo) enlaza al detalle que la explica (persona, hoja, pestaña) cuando existe.
- UX-35: la exportación avisa en su tooltip "Incluye correos reales: compártalo sólo con quien lo necesite".
