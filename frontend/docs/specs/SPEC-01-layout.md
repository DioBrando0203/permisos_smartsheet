# SPEC-01 Estructura de pantalla, navegación y estado del panel

Estado: borrador (fase F1)
Responsable del código: `components/layout/`, `app/router.tsx`, `app/App.tsx`, `features/shell/`
Relacionadas: ADR-01, ADR-04, ADR-07, ADR-08, SISTEMA_VISUAL; backend `GET /api/health`, `GET /api/me`

## Objetivo

Una pantalla estable donde siempre se sabe qué se está mirando, si el panel puede cambiar algo y cómo volver.

## Alcance

- Incluye: cabecera, navegación lateral con cinco destinos, banner de modo solo lectura, errores de conexión, rutas, responsive.
- Excluye: login (PEN-08), tema oscuro.

## Comportamiento

1. Cabecera de 48 px: "Permisos de Smartsheet", nombre de la cuenta (`account_name`) y de la persona dueña del token (`/api/me`).
2. Navegación: Hojas (`/hojas`), Personas (`/personas`), Diseñadores (`/disenadores`), Revisión (`/revision`), Comparar (`/comparar`). El activo con barra de marca y `aria-current="page"`. Un destino aún no construido muestra "Próximamente" (sólo durante el desarrollo por fases).
3. `/` redirige a `/hojas`; ruta desconocida: "Esta página no existe" con enlace a Hojas.
4. `GET /api/health` al arrancar y cada 60 s:
   - `read_only: true`: banner fijo bajo la cabecera, informativo (no de error): "Modo solo lectura: el panel no cambia nada en Smartsheet." (ADR-08).
   - `smartsheet: "missing_token"`: aviso a todo el ancho con el texto de `TOKEN_MISSING` y ninguna vista carga.
5. Si el backend no responde (`BACKEND_UNREACHABLE`): aviso a todo el ancho con el comando para iniciarlo y "Reintentar"; al volver, el aviso desaparece solo.
6. `SMARTSHEET_AUTH` en cualquier vista: el mismo aviso global con el texto de token rechazado.

## Estados

- Carga: esqueleto de cabecera mientras llega `/api/me`; la navegación ya es usable.
- Vacío: no aplica.
- Éxito: cabecera con cuenta y persona; banner si corresponde.
- Parcial: no aplica.
- Error: avisos globales de los puntos 4 a 6.

## Criterios de aceptación

- CA-01: la URL refleja la vista, la hoja o persona abierta y la pestaña; Atrás vuelve a la anterior. Prueba: e2e.
- CA-02: con `read_only: true` el banner aparece y los controles de escritura de cualquier vista están deshabilitados con el motivo. Prueba: componente con MSW.
- CA-03: con el backend caído aparece el aviso con "Reintentar" y no se muestran datos viejos como si fueran actuales. Prueba: componente con MSW (error de red).
- CA-04: `missing_token` bloquea las vistas con su aviso. Prueba: componente con MSW.
- CA-05: sin desborde horizontal a 320 px. Prueba: e2e visual.

## Accesibilidad

`<header>`, `<nav aria-label="Principal">`, `<main>`; enlace "Saltar al contenido"; banner con `role="status"`, avisos de error con `role="alert"`.

## Responsive

- 1180 o menos: navegación sólo con iconos (con etiqueta accesible y tooltip).
- 860 o menos: navegación abajo con los cinco iconos; maestro-detalle apilado con "Volver".
