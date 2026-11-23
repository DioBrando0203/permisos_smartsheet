# Uso de Smartsheet con navegador (Playwright) (PW-xx)

Estado 2026-11-23. Cómo se revisaron y configuraron en noviembre de 2026 las Dynamic Views, el formato condicional y el Admin Center, que la API pública de Smartsheet no permite, y cómo puede hacerlo una IA de nuevo (por ejemplo, la del equipo Linux). La herramienta y su instalación: `herramientas/smartsheet_ui/README.md`.

## Cuándo y con qué permiso

- PW-01: es una opción, no un paso obligatorio. La IA sólo la usa cuando el usuario lo autoriza expresamente en el chat para esa tarea; sin esa autorización, se lo propone y espera.
- PW-02: para qué sirve: lo que la API no hace: crear, renombrar y configurar Dynamic Views (tabla, panel, sólo lectura, obligatorios, `Field Logic`, restricción por usuario, compartir), leer y crear formato condicional, y pantallas del Admin Center (`API Insights`, permisos de automatizaciones). Lo que la API sí hace (filas, columnas, automatizaciones con el conector de Smartsheet) se hace por API.
- PW-03: escribir sólo en el workspace `Pruebas`; lo demás, sólo mirar (AGENTS.md). Nunca compartir, dejar de compartir ni borrar sin un OK explícito para eso; antes de borrar, documentar lo que se borra.
- PW-04: el usuario inicia sesión a mano; la IA nunca escribe contraseñas ni códigos, no imprime tokens (tampoco el `x-smar-xsrf` de PW-11) y no copia correos a docs ni a la bitácora.
- PW-05: todo cambio se comprueba releyendo después de guardar (o recargando la página) y se anota en la bitácora con lo que se hizo.

## Cómo se trabaja

- PW-06: se arranca `herramientas/smartsheet_ui` (`npm start`), el usuario entra a Smartsheet en la ventana que se abre, y la IA manda órdenes por `http://127.0.0.1:9334` (`/aria`, `/text`, `/shot` para mirar; `/clickrole`, `/type` para actuar; `/run` para scripts).
- PW-07: para saber qué hay en pantalla, `/aria` es mejor que una captura: da botones, campos y diálogos con su nombre. Las capturas sirven para confirmar colores o posiciones.
- PW-08: preferir clics por rol y nombre (`/clickrole`) antes que por coordenadas; las coordenadas cambian con el tamaño de la ventana y de una hoja a otra.
- PW-09: cerrar sin guardar todo diálogo que se abrió sólo para mirar (`Cancel`, `Discard`); si aparece un aviso del producto (por ejemplo, del Admin Center), cerrarlo sin cambiar opciones.

## Dynamic Views

- PW-10: pantallas: lista en `https://app.smartsheet.com/dynamicview/`; ajustes de una vista en `.../dynamicview/views/<id>/admin/basic`, con las pestañas `General`, `View Display`, `Details Panel` y `Sharing`.
- PW-11: la aplicación de Dynamic View tiene su propia API interna, que usa la misma pantalla y responde con la sesión del navegador: `GET /dynamicview/api/views` (lista, con el id del origen), `GET /dynamicview/api/views/{id}?include=config,shares,form,filters` (configuración), `GET .../{id}/sourcemetadata` (columnas con su título), `PUT /dynamicview/api/views/{id}` (guarda sólo lo que se manda: `name`, claves de `config`, o `form` completo con `fields` y `rules`) y `POST /dynamicview/api/views` con `{name, viewSourceType, viewSourceId}` (crea en blanco). Las escrituras exigen el encabezado `x-smar-xsrf`, que se toma de los pedidos de la propia página (sin él responde 401). Así trabajan `dv_apply.js`, `dv_create.js` y `dv_rename.js`: el mismo pedido que manda la pantalla al guardar.
- PW-12: `form.fields` lleva `columnId`, `ordinal`, `required`, `readOnly`, `hidden`; cada regla de `Field Logic` lleva `criteria` (columna, `HAS_ANY_OF` o `HAS_NONE_OF`, opciones) y `actions` con `actionType` `HIDE`, `READ_ONLY`, `EDITABLE` o `REQUIRE`. Toda columna usada en una regla debe estar en el panel.
- PW-13: `config` lleva `userColumnId` (restricción por usuario), `sheetFilterId` (filtro de hoja), `intakeSheetId` (permite agregar filas), `canDownload`, comentarios, adjuntos y `displayedFields` (la tabla).
- PW-14: en el árbol de accesibilidad, el desplegable `Restrict view by current user` se llama como su primera opción ("No restriction..."); la columna elegida es el texto que viene después. Leerlo mal dio un falso "sin restricción" el 2026-11-22.
- PW-15: en la pantalla, los interruptores `Require` y `Read-Only` no responden al clic por rol: hay que hacer clic en el interruptor visible; un campo del panel se agrega pasando el mouse sobre él y pulsando "Add ... to form"; reordenar exige arrastrar. Por eso conviene `dv_apply.js`.
- PW-16: antes de borrar una vista: buscar en las automatizaciones de todas las hojas y en los dashboards si alguien enlaza `dynamicview/views/<id>` (un aviso quedaría con el enlace roto) y confirmar el nombre en pantalla antes de pulsar `Delete View`.

## Formato condicional

- PW-17: el cuadro se abre con el botón `Conditional Formatting` de la barra de la hoja (su posición cambia según la hoja); las reglas nuevas se agregan al final y las de arriba ganan: crearlas en orden, con las de color de fila al final.
- PW-18: las listas de columnas, valores y "Select what to format" sólo dibujan lo visible: hay que desplazar la lista y buscar dentro de su recuadro (`cf_rule.js` lo hace). Una condición sólo puede elegir opciones de una lista o valores que ya existen en la hoja: para copiar reglas de estados, la columna tiene que ser lista desplegable.
- PW-19: se lee cada regla con `cf_read.js` (texto y colores de la muestra "abcde"); se guarda con OK en el cuadro y el ícono de guardar de la hoja; se comprueba recargando y leyendo de nuevo.

## Admin Center

- PW-20: `admin.smartsheet.com`: entrar desde el menú (la dirección directa de una sección puede volver al inicio); `API` muestra las llamadas de los últimos 30 días por endpoint y por usuario (así se evaluó el consumo, `KMV_2.0.md` K2-96); `Security Controls` tiene los permisos de automatizaciones. Sólo mirar.

## Lo que se hizo así (referencias)

- PW-30: revisión y correcciones de las vistas de la 2.0 y vistas nuevas (`VISTAS_KMV_2.0.md` VK-00t4 y VK-00t5).
- PW-31: colores de la maestra copiados a las hojas de equipo (VISTAS VK-60 a VK-65).
- PW-32: documentación y borrado de las vistas de prueba anteriores (`vistas_anteriores/`).
- PW-33: evaluación del consumo de API en `API Insights` (K2-96).
- PW-34: las automatizaciones no se hicieron con el navegador sino con el conector de Smartsheet de la IA (`create_workflow`, `update_workflow`), que sí las crea por API (`AUTOMATIZACIONES_KMV_2.0.md` AU-84).
