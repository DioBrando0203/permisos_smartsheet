# Reglas de estilos y diseño visual

Valores y uso de tokens en `estilos/SISTEMA_VISUAL.md`. Base: Fluent 2 (ADR-01).

## Tokens

- E-01: todo color, tamaño de fuente, interlineado, espaciado, radio, sombra y duración sale de un token de `tokens.css`. Prohibidos hex, rgb o px sueltos en reglas de componentes, salvo ajustes ópticos de 1 a 6 px.
- E-02: antes de crear un token, buscar uno existente. Un valor nuevo sale de la rampa de Fluent 2 y se documenta en `SISTEMA_VISUAL.md` en el mismo cambio.
- E-03: texto siempre con `--fg-1`, `--fg-2` o `--fg-3` (AA). Nunca grises más claros para texto.

## Organización del CSS

- E-04: un archivo por módulo en `src/app/styles/`, importado desde `global.css` en orden: tokens, base, ui, layout, features y responsive al final.
- E-05: máximo 250 líneas por archivo CSS; al superarlas, dividir por responsabilidad.
- E-06: especificidad baja y plana: máximo tres clases por selector, sin `!important` ni ids.
- E-07: estados con `is-*`, `aria-*` o `data-*`.
- E-08: media queries de tamaño en `responsive.css`, de mayor a menor; `prefers-reduced-motion` junto a la regla que modifican.

## Layout

- E-09: ningún contenido provoca scroll horizontal del documento. Hijos de flex y grid con texto llevan `min-width: 0`.
- E-10: textos variables (nombres de hoja, correos) con elipsis y el texto completo en `title`; en el detalle, `overflow-wrap: anywhere`.
- E-11: cada panel tiene su propio scroll; la cabecera de la tabla de permisos queda fija al desplazarse.
- E-12: densidad de tabla "media" de Fluent: filas de 44 px con ratón y 52 px con puntero táctil.

## Color con significado

- E-13: nivel de acceso con insignia neutra y un icono por nivel; el color no distingue niveles (no hay "rojo = administrador"). Ver E-17.
- E-14: rojo (`--danger-*`) sólo para acciones destructivas y errores; naranja (`--warning-*`) para avisos parciales; verde (`--success-*`) sólo en el aviso de éxito.
- E-15: heredado del workspace con estilo atenuado (`--fg-2`), insignia "Heredado" e icono de carpeta; propietario con icono de corona o llave y texto.

## Interacción y accesibilidad visual

- E-16: contraste AA: 4.5:1 en texto, 3:1 en texto grande e iconos funcionales.
- E-17: el color nunca es la única señal: estados con icono o texto.
- E-18: foco visible en todo interactivo (contorno de Fluent).
- E-19: todo control tiene hover, pressed y disabled; disabled conserva contraste legible para leer el motivo.
- E-20: objetivos táctiles de 24 px con ratón y 40 px con `pointer: coarse`.
- E-21: transiciones de 100 a 200 ms con `--curve-easy-ease`; nada se anima con `prefers-reduced-motion: reduce`.

## Marca

- E-22: tokens e iconos de Fluent 2 (MIT). Sin logotipos ni colores de marca de Smartsheet ni de Microsoft.
