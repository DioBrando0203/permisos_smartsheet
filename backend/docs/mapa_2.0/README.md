# Mapa de la KMV 2.0 (MP-xx)

Estado 2026-11-24. Guía corta para entender la 2.0 de un vistazo: qué hojas hay, cuál es la principal, qué vistas, reportes y automatizaciones se usan, qué hace el servicio (la API) y cómo fluye un proyecto de punta a punta. Todo está en el workspace `Pruebas`, carpeta `Producto/PROJECT KMV 2.0 - Prototype`. El detalle de cada regla sigue en `../KMV_2.0.md` (K2-xx), que es la fuente del estado.

## La 2.0 en una página

- MP-01: hay una hoja principal, la maestra `PROJECT KMV 2.0 (Prototype)`, con los proyectos de todas las compañías (una maestra por año). Cada proyecto es una fila madre; cada trámite (permiso, línea, MOT) es una fila hija debajo de su proyecto.
- MP-02: el trabajo de cada equipo vive en su propia hoja (permisos, MOT y paquetes, Records, facturación, Design Tickets). Esas hojas las llena el servicio; nadie crea filas a mano en ellas.
- MP-03: la gente no trabaja en las hojas sino en vistas (Dynamic Views): la coordinadora crea proyectos y trámites en la maestra; cada equipo ve sólo lo suyo en la vista de su hoja.
- MP-04: Smartsheet hace solo lo que puede: fórmulas (IDs visibles, días, fase, cerrado, acceso del cliente), formato de colores y automatizaciones de aviso.
- MP-05: el servicio (backend, usa la API de Smartsheet) hace lo que Smartsheet no puede: numerar proyectos, poner cada trámite bajo su proyecto, crear y mantener las filas en las hojas de equipo, devolver los resultados a la maestra, copiar las conversaciones a `Obs` y avisar cambios de metraje.
- MP-06: Smartsheet es la fuente de verdad. El servicio sólo guarda en su base (PostgreSQL) los contadores de IDs y lo técnico; nada técnico se escribe en las hojas.

## Archivos

- `README.md`: esta página.
- `HOJAS_Y_PIEZAS.md`: hojas (principal, de equipo y listas), vistas, reportes, automatizaciones y qué depende del servicio (MP-10 a MP-59).
- `SERVICIO_Y_FLUJO.md`: qué hace el servicio con la API, cómo corre, qué pasa si se apaga y el flujo de un proyecto paso a paso (MP-60 a MP-99).
- `DIAGRAMAS.md`: cinco diagramas (hojas, vistas, flujo de un proyecto, ciclo del servicio y qué depende de él), en Mermaid: GitHub y VS Code los dibujan (MP-D1 a MP-D5).

## Dónde está el detalle

- Estado completo y pendientes: `../KMV_2.0.md`.
- Cómo se arma cada vista: `../VISTAS_KMV_2.0.md`.
- Lista de automatizaciones y para qué sirve cada una: `../AUTOMATIZACIONES_2.0_RESUMEN.md`; guía con el porqué: `../AUTOMATIZACIONES_KMV_2.0.md`.
- Reglas del servicio: SPEC-B18 (Records), SPEC-B19 (Billing y metraje), SPEC-B20 (hojas de equipo), SPEC-B21 (registro y consumo de API), SPEC-ID01 (IDs, en `servicios/ids/SPEC.md`).
- Vistas de prueba anteriores, ya documentadas: `../vistas_anteriores/`.
