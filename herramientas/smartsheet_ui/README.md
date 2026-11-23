# Navegador de Smartsheet con Playwright (smartsheet_ui)

Herramienta opcional para que una IA (o una persona) revise o cambie en Smartsheet lo que la API pública no permite: Dynamic Views, formato condicional y pantallas del Admin Center. Abre un Chrome real con la sesión del usuario y recibe órdenes por HTTP en la propia máquina. Reglas de uso, permisos y lo aprendido: `backend/docs/PLAYWRIGHT_SMARTSHEET.md` (PW-xx). Sólo se usa con autorización expresa del usuario.

## Instalar (Linux)

- Requisitos: Node.js 20 o más y un escritorio (el navegador se abre en pantalla para que el usuario inicie sesión).
- Desde esta carpeta: `npm install` y luego `npx playwright install --with-deps chromium` (la segunda instala el navegador y sus librerías; puede pedir `sudo`).

## Arrancar

- `npm start` (o `node pwserver.js`). Se abre Chrome en `app.smartsheet.com`.
- La primera vez el usuario inicia sesión a mano (correo, contraseña y verificación). La IA nunca escribe contraseñas ni códigos. La sesión queda guardada en el perfil y las veces siguientes ya entra.
- Escucha en `http://127.0.0.1:9334` (sólo esta máquina).
- Variables opcionales: `PW_PORT` (puerto), `PW_PROFILE` (perfil; por defecto `~/.config/galp_smartsheet_ui/profile`, fuera del repo), `PW_SHOTS` (capturas; por defecto la carpeta temporal), `PW_SCRIPTS` (scripts; por defecto `scripts/`), `PW_START` (página inicial).
- Para cerrar: cerrar la ventana de Chrome o detener el proceso.

## Órdenes (HTTP GET)

- `/state`: pestañas abiertas y su dirección.
- `/goto?url=...&wait=7000`: abre una dirección.
- `/text?n=5000`: texto visible de la página.
- `/aria?sel=body&n=8000`: árbol de accesibilidad (botones, campos, diálogos con su nombre): la mejor forma de saber qué hay en pantalla.
- `/shot?name=x&full=1`: captura de pantalla (devuelve la ruta del archivo).
- `/click?t=Texto&exact=1&i=0`, `/clickrole?role=button&name=Save&exact=1`, `/clickxy?x=..&y=..`: clics.
- `/type?t=...`, `/key?k=Escape`, `/scroll?x=..&y=..&dy=600`, `/drag?x1=..&y1=..&x2=..&y2=..`, `/box?t=Texto`: teclado, rueda, arrastre y posición de un texto.
- `/eval?f=archivo.js`: corre en la página un script que devuelve un valor (los `cf_*.js` de lectura).
- `/run?f=archivo.js&arg=archivo.json` (o `&argjson=...`): corre un script con `page` (Playwright) y `arg`; los `dv_*.js` y `cf_rule.js`.
- `tab=N` en cualquier orden elige la pestaña (por defecto, la última).

Ejemplo: `curl -s "http://127.0.0.1:9334/run?f=dv_list.js"`.

## Scripts (`scripts/`)

- `dv_list.js` (lectura): todas las Dynamic Views de la cuenta con su origen.
- `dv_dump.js` (lectura): configuración de vistas con títulos de columna; `arg = {"ids": ["..."]}`. Sin correos.
- `dv_create.js` (escribe): crea una vista en blanco sobre una hoja o reporte de Pruebas; `arg = {"source": "<nombre exacto>"}`; se niega si el resultado no está en Pruebas.
- `dv_rename.js` (escribe): renombra una vista; `arg = {"id", "expect" (nombre actual), "name"}`.
- `dv_apply.js` (escribe): nombre, restricción por usuario, ajustes, tabla y panel (con sólo lectura, obligatorios y reglas de `Field Logic`); `arg = {"id", "expect", "name"?, "userColumn"?, "config"?, "table"?, "panel"?, "rules"?, "dry"?}`. Con `"dry": true` sólo muestra lo que mandaría. Relee y devuelve cómo quedó.
- `cf_read.js` (lectura, `/eval`): reglas del cuadro `Conditional Formatting` abierto, con sus colores.
- `cf_palette.js` (lectura, `/eval`): colores del menú de colores abierto.
- `cf_rule.js` (escribe, con el cuadro abierto; no guarda): crea una regla de formato; `arg = {"column", "values", "target": "row" | "<columna>", "bold", "strike", "bg", "fg"}`. Después se pulsa OK en el cuadro y Save en la hoja.

## Seguridad

- El perfil guarda la sesión de Smartsheet: no se copia, no se comparte y no entra al repositorio.
- Las capturas pueden mostrar datos reales: se borran al terminar y no se suben.
- Los scripts no imprimen tokens; los de lectura no devuelven correos.
