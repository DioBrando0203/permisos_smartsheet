# SPEC-04 Personas

Estado: aprobada (F2: detalle y simulación de revocación implementados; ejecutar la revocación real en F5)
Responsable del código: `features/people/`
Relacionadas: backend SPEC-B03 y SPEC-B06; ADR-06, ADR-08, ADR-12; UX-19, UX-29, UX-30

## Objetivo

Saber a qué hojas tiene acceso una persona o grupo, desde cuándo no entra y retirarla de varias hojas de una vez cuando corresponda.

## Comportamiento

### Directorio `/personas`

1. `GET /api/users` una vez (ADR-12). Por persona: avatar, nombre (o correo), correo, cantidad de hojas, nivel más alto e insignias: "Organización", "Contacto", "(usted)"; los usuarios de la organización muestran "Última conexión hace X" (`last_login`).
2. Filtros rápidos en el navegador: Todos, Con acceso, Sin acceso (contactos sin hojas), Organización, Externos, Contactos, Grupos. Buscador (UX-21).
3. Orden: más hojas primero.
4. Primera carga lenta (lee todas las hojas): LoadingNotice "Leyendo permisos de todas las hojas…" (UX-29).
5. "Exportar a Excel" (enlace a `GET /api/export/access.csv`, K-09).

### Detalle `/personas/:key`

1. `GET /api/users/{key}` (`key` con `encodeURIComponent`).
2. Cabecera: nombre, correo, insignias, última conexión, cantidad de hojas.
3. Tabla de sus hojas: hoja (enlace a SPEC-05), nivel, origen y acciones de SPEC-03 (cambiar nivel, quitar) con los mismos bloqueos (ADR-06). Una hoja con propio y heredado aparece una vez con los dos orígenes.

### Quitar de varias hojas

1. Botón "Quitar de varias hojas" en el detalle.
2. Diálogo: lista de sus hojas con casillas (todas marcadas por defecto); las bloqueadas (propietario, heredado, sin permiso) aparecen sin casilla y con el motivo.
3. "Ver qué pasaría" llama a `POST /api/users/{key}/revoke` con `dry_run: true` y muestra la simulación: cuántas se quitarían y cuáles se omiten y por qué (UX-30). Funciona en modo solo lectura.
4. "Quitar de N hojas" (`danger`) ejecuta con `dry_run: false` tras confirmación reforzada (escribir el nombre o correo de la persona). Resultado por hoja: hecho o falló con su motivo. Deshabilitado en modo solo lectura (UX-28).

## Estados

- Carga: esqueleto con el aviso de la primera carga.
- Vacío: "Nadie más tiene acceso a las hojas" o "Nadie coincide con el filtro".
- Éxito: lista y detalle.
- Parcial: `incomplete: true`: StatusAlert de advertencia "No se pudieron leer N hojas" con la lista y "Reintentar" (UX-19).
- Error: StatusAlert con texto por código y "Reintentar".

## Criterios de aceptación

- CA-01: los filtros rápidos aplican la condición correcta (por ejemplo, Externos = `is_org_member=false` y tipo usuario). Prueba: unitaria.
- CA-02: parcial muestra datos y aviso a la vez. Prueba: componente con MSW.
- CA-03: la simulación de quitar de varias hojas se puede hacer con `read_only: true` y no ejecuta nada; el botón de ejecutar está deshabilitado con el motivo. Prueba: componente con MSW.
- CA-04: quitar acceso desde la persona invalida también la vista de esa hoja (`invalidateAfterShareWrite`). Prueba: componente con MSW.
- CA-05: una clave con `@` funciona en la URL y al recargar. Prueba: e2e.
