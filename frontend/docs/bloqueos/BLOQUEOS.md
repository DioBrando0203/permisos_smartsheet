# Bloqueos y problemas conocidos (frontend)

Formato: ID, fecha Lima, síntoma, causa, solución o prevención, estado. Incluye hechos del backend y de Smartsheet que la interfaz debe respetar.

## FB-01 Mismo id en el permiso propio y el heredado

Fecha: 2026-10-16. Estado: a prevenir desde F1. Origen: B-05 del backend.
Síntoma esperable: advertencia de React por claves repetidas o una persona que "desaparece" al agrupar.
Prevención: clave `id + scope` (P-36) y agrupar por persona con `groupShares` (SPEC-03 CA-01).

## FB-02 Cargas largas en la primera lectura

Fecha: 2026-10-16. Estado: a prevenir desde F2.
Hecho: directorio 3 a 5 s, revisión 5 s, diseñadores 14 s, automatizaciones de la cuenta 17 s, historial de fila hasta 11 s (backend, cuenta real).
Prevención: `LoadingNotice` (UX-29), plazo de 120 s (P-33), no cancelar al cambiar de vista, `staleTime` largo en las lentas (P-32).

## FB-03 Personas sin nombre

Fecha: 2026-10-16. Estado: a prevenir desde F1. Origen: B-03 del backend.
Prevención: mostrar el correo como nombre (UX-25); avatar con la inicial del correo.

## FB-04 Dynamic View no aparece

Fecha: 2026-10-16. Estado: límite honesto. Origen: B-07 del backend.
Prevención: lenguaje de UX-32 e insignia "Vista dinámica" según `has_dynamic_view`.

## FB-05 Hojas de otra persona

Fecha: 2026-10-16. Estado: a prevenir desde F1. Origen: PEN-14 del backend.
Hecho: 4 hojas con `in_my_list: false`, `access_level: null`, sin `permalink` ni `modified_at`; escribir en ellas responde `NOT_SHARED_WITH_TOKEN`.
Prevención: UX-33; no mostrar "Abrir en Smartsheet" ni fecha cuando faltan.

## FB-06 Estados "cerrados" supuestos

Fecha: 2026-10-16. Estado: abierto (PEN-27 del backend).
Hecho: la carga de diseñadores depende de `APP_CLOSED_STATUSES`, que aún no confirmó el usuario.
Prevención: mostrar siempre qué estados se consideran cerrados y permitir cambiarlos en la vista (SPEC-08).
