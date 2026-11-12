# SPEC-B17 Conversaciones de cada fila compiladas en Obs

Estado: en uso en Pruebas (2026-11-12, PEN-46); migración 004 aplicada y prueba real correcta en PROJECT KMV (CA-03 y CA-07 comprobados también en real).

## Objetivo

- OB-01: el equipo deja de escribir el avance a mano en `Obs` y comenta en la conversación de cada fila (hoja o Dynamic View). El servicio copia cada comentario nuevo a `Obs` con el formato de siempre, para que la descarga CSV de la Dynamic View y la exportación a Excel de un reporte lleven todo el historial, como hoy.
- OB-02 (ADR-B15): Smartsheet no exporta las conversaciones junto a cada fila (la descarga CSV de una Dynamic View no las trae; la exportación a Excel las pone en otra pestaña). La columna `Obs` sigue siendo de Smartsheet y editable; el servicio sólo agrega texto.

## Reglas

- OB-03: formato `MM.DD - texto` con la fecha del comentario en `APP_OBS_TIMEZONE` (por defecto `America/Lima`), sin autor y lo más reciente arriba. Comentarios del mismo día en una línea, en orden, separados por ` // `; los saltos de línea de un comentario también se unen con ` // `.
- OB-04: agrega, nunca reemplaza. Los comentarios se aplican uno a uno en orden cronológico. Cada línea con fecha entra arriba, debajo de los títulos que encabezan `Obs` (OB-16); si esa primera línea con fecha es del mismo día (empieza con `MM.DD -`), se le agrega ` // texto` al final en vez de crear otra línea. Lo que ya había, o lo que alguien escriba a mano, se conserva.
- OB-05: cada comentario se agrega una sola vez. Los ya incorporados se guardan en PostgreSQL (`obs_comentario`, migración 004) como estado técnico. Editar o borrar un comentario después no cambia `Obs`.
- OB-06: no se copian comentarios vacíos, los que empiezan con `#interno` o `#internal` (sin distinguir mayúsculas) ni los del archivo del servicio (OB-07). Sólo conversaciones de filas; las de la hoja se ignoran.
- OB-07: límite de 4 000 caracteres por celda. Si el resultado lo supera, las líneas más antiguas (abajo) pasan a un comentario nuevo de la fila que empieza con `[Obs archive]` (en partes de hasta 4 000 caracteres) antes de escribir `Obs`. Una línea sola más larga que el límite se recorta en `Obs` con `…` y se archiva completa. No se pierde texto.
- OB-08: escritura por fila: lectura fresca de la fila, composición y `PUT` sólo de la celda `Obs`. Si la escritura falla con error del servidor o sin respuesta, se relee la fila: si `Obs` ya tiene el valor compuesto se registra; si no, se reintenta en el siguiente ciclo. Un error 4xx no registra nada.
- OB-09: no es atómico frente a otros editores: si alguien edita `Obs` entre la lectura y la escritura (segundos), su cambio puede perderse. Cada escritura figura como del administrador en `Modified By` (SPEC-B08); sólo se escriben filas con comentarios nuevos.
- OB-16 (pedido del usuario, 2026-11-12): títulos de sección. Un comentario que empieza con `**` se copia tal cual, sin fecha, como primera línea de `Obs`; si había texto debajo, queda una línea en blanco entre el título y la sección anterior. Los comentarios con fecha posteriores entran debajo de las líneas `**` seguidas del principio, de modo que un título nuevo abre una sección arriba y las secciones anteriores quedan debajo con sus mensajes. Así también se respetan los títulos escritos a mano arriba de `Obs`, como en el tracker original (76 de 79 celdas con `**` lo tienen en la primera línea). Si el mismo día hay un chat, luego un título y luego otro chat, la línea en blanco evita unirlos en la misma línea.

## Barreras

- OB-10: `APP_OBS_SYNC_ENABLED=true` y las barreras de escritura del ID Manager (`APP_READ_ONLY=false`, `IDS_WRITES_ENABLED`, `IDS_TRANSITION_APPROVED`). Sin ellas no se construye el paso.
- OB-11: sólo hojas configuradas del ID Manager (`pilot.SHEETS`, hoy PROJECT KMV) y en el workspace Pruebas, comprobado en cada pasada; la columna `APP_OBS_COLUMN` (por defecto `Obs`) debe existir una sola vez.

## Ejecución y carga

- OB-12: corre al final de cada ciclo del procesador en modo asignación, como máximo cada `APP_OBS_INTERVAL_SECONDS` (30 s por defecto), y escribe como máximo `APP_OBS_MAX_ROWS` filas por pasada (20); el resto queda para la siguiente. Un fallo queda en `last_obs_sync` de `/api/ids/status` y no afecta a los IDs ni al catálogo.
- OB-13: por pasada: una lectura del workspace, una de columnas, las páginas de conversaciones (100 por página) y una consulta a PostgreSQL; por fila con comentarios nuevos, un GET y un PUT (más un POST si archiva). Límite de la API: 300 solicitudes por minuto por token.

## Contrato con Smartsheet (verificado con GET el 2026-11-12)

- OB-14: `GET /sheets/{id}/discussions?include=comments` paginado: cada conversación trae `parentType` (`ROW` o `SHEET`), `parentId` (fila) y `comments` con `id`, `text` y `createdAt` en UTC. Un comentario escrito en el panel crea una conversación nueva por comentario; las respuestas son comentarios de la misma conversación.
- OB-15: escrituras según la documentación oficial: `PUT /sheets/{id}/rows` (celda `Obs`) y `POST /sheets/{id}/rows/{rowId}/discussions` con `{"comment": {"text": ...}}`, cuya respuesta trae `result.comments[0].id`.

## Criterios de aceptación

- CA-01: formato, agrupación por día con ` // `, unión con la primera línea del mismo día, zona horaria y orden.
- CA-02: comentarios `#interno`, vacíos, del archivo y de la hoja no se copian.
- CA-03: segunda pasada sin comentarios nuevos no escribe; un comentario nuevo se agrega una sola vez.
- CA-04: más de 4 000 caracteres: archiva lo más antiguo en un comentario y `Obs` queda dentro del límite sin perder texto.
- CA-05: error 500 con el valor aplicado se registra tras releer; sin aplicar no se registra.
- CA-06: sin barreras, con hoja fuera de Pruebas o sin la columna no escribe nada.
- CA-07: el procesador guarda el resultado en `last_obs_sync` y un fallo no detiene el ciclo.
- CA-08: un comentario `**` abre una sección arriba con línea en blanco; los comentarios siguientes entran debajo del título (unidos por día) y debajo de los títulos escritos a mano.
