# SPEC-01 Estructura de pantalla y navegación

Estado: borrador
Responsable del código: `components/layout/AppLayout.tsx`, `app/routes.tsx`
Relacionadas: ADR-01, ADR-04, SISTEMA_VISUAL

## Objetivo

Una pantalla estable donde siempre se sabe en qué hoja o persona se está y cómo volver.

## Alcance

- Incluye: cabecera, navegación lateral, maestro-detalle, rutas, responsive.
- Excluye: login (PEN-08), tema oscuro.

## Comportamiento

1. Cabecera de 48 px: nombre del panel ("Permisos de Smartsheet"), nombre de la cuenta y de la persona dueña del token (de `/api/me`).
2. Navegación lateral con dos destinos: Hojas (`/hojas`) y Personas (`/personas`). El activo se marca con barra de marca y `aria-current="page"`.
3. `/` redirige a `/hojas`.
4. Cada destino es maestro-detalle: lista a la izquierda, detalle a la derecha; sin selección, el detalle muestra un estado vacío que invita a elegir.
5. Ruta desconocida: estado vacío "Esta página no existe" con enlace a Hojas.

## Estados

- Carga: esqueleto de cabecera mientras llega `/api/me`; la navegación ya es usable.
- Vacío: detalle sin selección.
- Éxito: cabecera con cuenta y persona.
- Parcial: no aplica.
- Error: si `/api/me` falla con `SMARTSHEET_AUTH` o `TOKEN_MISSING`, aviso a todo el ancho: "El panel no puede conectarse con Smartsheet. Revise el token en backend/.env." Las vistas no se cargan.

## Criterios de aceptación

- CA-01: la URL refleja la hoja o persona abierta y Atrás vuelve a la anterior. Prueba: e2e.
- CA-02: sin desborde horizontal a 320 px. Prueba: e2e visual.
- CA-03: error de token muestra el aviso y no intenta cargar hojas. Prueba: componente con MSW.

## Accesibilidad

`<header>`, `<nav aria-label="Principal">`, `<main>`; enlace "Saltar al contenido".

## Responsive

- 1180 o menos: navegación sólo con iconos.
- 860 o menos: lista o detalle (no ambos), botón Volver en el detalle, navegación abajo.
