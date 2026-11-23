# Vistas sobre la copia de Blue Stream 2026 (VA-20 a VA-29)

Hoja `Copy of 8. Blue Stream - Engineering Plan 2026` (`7379849166671748`, Pruebas): copia de la hoja de producción de Blue Stream para probar vistas sin tocar la real. Según el usuario funcionaban bien. Ninguna automatización de la cuenta enlaza a estas vistas. Estado: se borran (README VA-09); la hoja copia se queda.

## VA-20 `Blue Stream - Designers`

- Id `51d1c4e3-65a8-4903-8175-7a368de5af4f`; último uso de la cuenta dueña 2026-11-11.
- Restricción por usuario: `Correo Designer1`. Sin filtros.
- Tabla (11): `Priority`, `Type of Project`, `Tracking Project`, `Project Name`, `Project Address`, `City`, `County`, `Drawing Due Date`, `Record Box`, `Design Ticket`, `Project Status`.
- Panel (1): `Project Status`.
- Comentarios visibles sin poder agregar; adjuntos visibles sin poder agregar; sin exportar.
- Compartida con `DV Designers`.

## VA-21 `Blue Stream Permit`

- Id `da17e50a-fe0d-4da7-994c-f516ae283036`; último uso 2026-11-02. Pese al nombre, es una vista de Records.
- Restricción por usuario: `Correo Designer2`.
- Filtro de vista compartido `335`: `Tracking Project` `is one of` `KMV-BS-26-335` (prueba con un solo proyecto).
- Tabla (17): `Tracking Project`, `Project Name`, `Project Address`, `City`, `County`, `Date Received`, `Agency`, `Design Ticket`, `Record Request`, `Record ID`, `LT Records`, `Record Received`, `Records Status`, `Record Box`, `Record # Days`, `Project Status`, `Obs`.
- Panel (7): `Record Request`, `Record Received`, `LT Records`, `Records Status`, `Record ID`, `Design Ticket`, `Obs`.
- Comentarios y adjuntos visibles y se pueden agregar; sin exportar.
- Compartida con `DV Permit Team`.

## Qué funcionó y qué pasó a la 2.0

- VA-22: probar sobre una copia de la hoja real fue seguro y dio el mismo resultado que en producción; en la 2.0 todo vive en la carpeta del prototipo dentro de Pruebas.
- VA-23: la columna de correo con nombre en español (`Correo ...`) era propia de la copia; en la 2.0 todo lo que se crea en Smartsheet va en inglés.
