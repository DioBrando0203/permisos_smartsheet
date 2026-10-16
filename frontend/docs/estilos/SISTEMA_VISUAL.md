# Sistema visual

Base: Fluent 2 (repositorio `microsoft/fluentui`, licencia MIT), el mismo que usa el proyecto de referencia `extractor_metadata`. `tokens.css` se copia de `extractor_metadata/frontend/src/app/styles/tokens.css` (rampas de marca, neutros, estados, avatares, tipografía, espaciado, radios, sombras y movimiento ya verificados) y se recorta a lo que usa este panel; los tokens propios de este panel se agregan con el mismo formato. Este documento explica su uso; si difieren, corregir en el mismo cambio.

## Principios

- Herramienta de administración: densa pero legible, neutra, sin decoración. Los datos (personas y niveles) son protagonistas.
- Paneles blancos redondeados sobre lienzo gris claro, como Microsoft 365 Admin.
- Color con significado: azul de marca para acción y selección, rojo sólo para destruir o error, naranja para avisos, verde sólo para confirmar éxito.
- Tema claro en la primera versión; los tokens se nombran por función para permitir tema oscuro después.

## Color

- Marca (rampa brandWeb): `--brand-80` #0f6cbd primario y selección; `--brand-70` hover y enlaces; `--brand-60` pulsado; `--brand-160` fondo de fila seleccionada y del buscador.
- Texto: `--fg-1` #242424 principal; `--fg-2` #424242 secundario y heredados; `--fg-3` #616161 metadatos y fechas.
- Fondos: `--bg-1` #ffffff paneles; `--bg-1-hover` #f5f5f5; `--bg-1-pressed` #e0e0e0; `--bg-2` #fafafa cabecera de tabla; `--bg-4` #f0f0f0 lienzo.
- Bordes: `--stroke-1` #d1d1d1 controles; `--stroke-2` #e0e0e0 tarjetas y separadores de filas.
- Estados: `--danger-bg` #fdf6f6, `--danger-border` #f1bbbc, `--danger-fg` #bc2f32; `--warning-bg` #fff9f5, `--warning-border` #fdcfb4, `--warning-fg` #bc4b09; `--success-bg` #f1faf1, `--success-border` #9fd89f, `--success-fg` #0e700e.
- Avatares: 10 tonos de la paleta de personas de Fluent (fondo tint40, texto shade30), por hash estable del correo.

## Tipografía

- `--font-base`: "Segoe UI", system-ui, sans-serif (sin fuentes web).
- Rampa Fluent (tamaño/interlineado): 200 12/16 metadatos, correos y fechas; 300 14/20 base, filas y botones; 400 16/22 títulos de panel; 500 20/28 nombre de la hoja en el detalle; 600 24/32 título de página.
- Pesos: 400 texto, 600 nombres de persona, títulos y botones.

## Espaciado, forma y movimiento

- Escala: `--space-xs` 4, `s` 8, `m` 12, `l` 16, `xl` 20, `xxl` 24, `xxxl` 32.
- Radios: `--radius-md` 4 (controles, insignias), `--radius-xl` 8 (paneles y diálogos), `--radius-circular`.
- Sombras: `--shadow-2` paneles, `--shadow-16` menús y Toast, `--shadow-64` diálogos.
- Movimiento: `--duration-faster` 100 ms, `--duration-normal` 200 ms, `--curve-easy-ease`.

## Dimensiones

- `--header-h` 48; navegación lateral `--nav-w` 220 (68 compacta bajo 1180).
- Lista maestra `--list-w` 360 (320 bajo 1180).
- Controles: `--control-sm` 24, `--control-md` 32, `--control-lg` 40.
- Filas de tabla: 44 (52 con `pointer: coarse`). Avatar 32 en filas, 40 en cabecera de persona.
- Diálogos: ancho máximo 560 (compartir) y 440 (confirmar).

## Niveles de acceso

- Insignia neutra (`--bg-2`, borde `--stroke-2`, texto `--fg-1`) con icono por nivel: Visor ojo, Comentarista globo de comentario, Editor lápiz, Editor que comparte lápiz con persona, Administrador escudo, Propietario corona (iconos de `@fluentui/react-icons`).
- Heredado: insignia "Heredado" con icono de carpeta, texto en `--fg-2`.

## Severidad, estados de automatización y fases

- Severidad (`lib/severity.ts`): alta con `--danger-*` e icono de alerta; media con `--warning-*` e icono de advertencia; informativa con `--info-*` e icono de información. Siempre icono más texto (E-17).
- Automatizaciones: "Funciona" `--success-fg` con check; "Con problemas" `--warning-fg`; "Apagada" `--fg-3` con icono de pausa.
- Fases de "Project Status" en `MeterBar`: una rampa neutra de marca (`--brand-140` a `--brand-60`) para las fases 1 a 9 y `--bg-6` para "otra"; el número de cada tramo visible en la leyenda (ADR-09).
- Insignias nuevas: "De otra persona", "Vista dinámica", "Organización", "Contacto", "Personal" (dominio), "Inactiva", "Sin acceso" (advertencia).

## Breakpoints

- 1180 o menos: navegación compacta (sólo iconos con etiqueta accesible); lista 320.
- 860 o menos: maestro-detalle apilado; navegación abajo; paneles sin radio ni sombra.
- 640 o menos: la tabla de permisos pasa a lista de tarjetas (persona arriba, nivel y acciones abajo); el correo en línea propia.

## Componentes (`components/ui`)

- Button: `primary` (una por zona), `secondary`, `subtle`, `danger`; tamaños `md` 32 y `sm` 24; `IconButton` exige `aria-label`.
- SearchBox: 32 de alto, icono de lupa, botón borrar, fondo `--brand-160` que pasa a blanco al enfocar.
- Select: nativo con estilo Fluent; opciones con etiqueta y descripción en `AccessLevelSelect`.
- Dialog y ConfirmDialog: `<dialog>` nativo, título, cuerpo, pie con botones a la derecha (el primario al final).
- Toast: `--shadow-16`, icono de estado, texto `--fg-1`, cierre manual, 5 s.
- StatusAlert: MessageBar de Fluent; icono con color, texto en `--fg-1`.
- Badge: insignia de nivel u origen.
- Avatar: iniciales o icono de grupo; decorativo.
- Skeleton, Spinner, EmptyState.
- Tabs: subrayado de marca de 3 px en la activa, 40 de alto, desplazable en móvil.
- StatTile: cifra en rampa 600 (24/32) y etiqueta en 200 (12/16), fondo `--bg-1`, borde `--stroke-2`, `--radius-xl`; se agrupan en una fila que pasa a 2 columnas bajo 640 px.
- MeterBar: barra horizontal de 8 px con tramos y leyenda con valores; sin tooltips como única fuente del número.
- LoadingNotice: Spinner pequeño y texto `--fg-2`; aparece a los 3 s (UX-29).
- CopyText: texto `--font-mono` 12/16 con botón "Copiar" (para `ref_id`).
- ReadOnlyBanner: franja `--info-bg` con borde inferior `--info-border`, icono de candado y texto `--fg-1`, 40 de alto.
