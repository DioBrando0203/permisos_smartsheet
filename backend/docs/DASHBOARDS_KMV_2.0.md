# Dashboards de la 2.0: guía y estado

Dashboards por año para la 2.0, inspirados en los de producción y armados en `Pruebas`. Decisión y propuesta: `KMV_2.0.md` K2-105 y K2-106.

## Referencia de producción (sólo lectura)

- DB-01: en producción, workspace `Workspace`, carpeta `Main Dashboard`:
  - `DASHBOARD HUB` es un menú: un título y 12 imágenes, cada una con enlace a un dashboard.
  - Hay una carpeta por tema y año. Cada una tiene el dashboard, una hoja `Metrics` con `COUNTIFS` entre hojas contra cada hoja de cliente del año, y a veces un reporte.
- DB-02: copias leídas con Playwright, el 2026-11-25. Están en `Pruebas/Producto/PROJECT KMV 2.0 - Prototype/Dashboards/Reference - Production copies` (`4281468374542212`), con el prefijo `REF |`.
  - Son 13: el `HUB`, `Zayo`, `Blue Stream`, `Lightpath` y `Breezeline Projects 2026`, `Dashboard Projects 2026`, `Production Designers 2026`, `Dashboard Permitting by customer`, `Production KMV 2026`, `Engineering & Permitting – All Customer`, y `Enterprise`, `Relocation` y `Special Projects Production 2026`.
  - Siguen mostrando datos de producción, porque sus widgets apuntan a las hojas originales. No tienen avisos.
- DB-03: indicadores que usan:
  - Por cliente: totales de proyectos, permisos y MOT; proyectos por mes comparando años; por condado; terminado contra no terminado; metraje.
  - Permisos: propios contra por terceros, y primera revisión.
  - Días promedio: diseño terminado, aprobación del PM y permiso enviado.
  - Por categoría (`Task`): Jumper, Relocation, Enterprise, OSP, ISP, LV.
  - MOT por estado; por `Construction Manager`; por diseñador y por persona de permisos (cantidad, metraje y días).
  - Lista de proyectos no terminados.

## Datos de la 2.0 (hecho el 2026-11-25)

- DB-10: carpeta `Pruebas/Producto/PROJECT KMV 2.0 - Prototype/Dashboards`:
  - `Dashboards`: `3155568467699588`.
  - `2026`: `200081212237700`.
- DB-11: hojas `KMV 2.0 Metrics 2026 - <nombre>`, creadas por `servicios/dashboards/metricas_anuales.py`:
  - `Customers`: una fila por cliente más `All customers`. Proyectos (total, activos, terminados, cancelados), permisos (lo mismo y por terceros), MOT, metraje, días promedio (diseño, aprobación del PM, permiso enviado), permisos con primera revisión, pedidos de Records y recibidos, y facturas (sin facturar, en curso, enviadas, cobradas).
  - `Months`: cliente × mes. Proyectos, permisos, MOT y metraje del año.
  - `Counties`: cliente × condado (Dade, Broward, Palm Beach, St Lucie, Martin, Orange y Others). Proyectos, permisos y MOT.
  - `Categories`: cliente × categoría de `Task`. Proyectos, cancelados, metraje y días promedio.
  - `People`: personas activas de `Contact List` con equipo `Design` o `Permits`. Proyectos y metraje diseñados, días de diseño, permisos asignados y días de permiso enviado.
- DB-12: cómo están hechas:
  - Fórmulas de columna, sin celdas fijas: un cliente o una persona nueva es una fila nueva.
  - Las referencias entre hojas van a columnas enteras de la maestra, `Permits`, Records y `Billing` (prefijos `M`, `P`, `R` y `B`).
  - Comprobado: 0 celdas con error, y conteos iguales a los de la maestra (2 proyectos, 5 permisos, 1 MOT, 2 diseños y 9 permisos asignados).
- DB-13: lo que aprendimos de Smartsheet:
  - `AVERAGEIFS` no se acepta en fórmulas de columna (error 1310); se usa `AVG(COLLECT(...))`.
  - Las referencias entre hojas traen el nombre del contacto, no el correo: las personas se reconocen por nombre o por correo.

## Año siguiente (2027)

- DB-20: pasos:
  1. Crear la carpeta `2027`.
  2. Desde `backend/`, correr `.venv/bin/python ../servicios/dashboards/metricas_anuales.py --year 2027 --folder <id de 2027> --master <maestra 2027> --previous-master <maestra 2026>`, más `--permits`, `--records` y `--billing` si las hojas de equipo cambian.
  3. `Months` trae también la columna `Projects 2026`, para comparar los dos años.
- DB-21: el script no toca hojas que ya existen y no crea nada fuera de `Pruebas`.

## Pendiente

- DB-30: armar los dashboards de 2026 sobre estas hojas:
  - O bien copiar las referencias `REF |` y apuntar sus widgets a las hojas nuevas con Playwright.
  - O bien crear gráficos con el conector; se arman sobre hojas, no sobre reportes.
  - Más el `HUB 2.0`, con sus imágenes enlazadas.
- DB-31: las filas de equipo cuya fila de la maestra se borró siguen contando en las métricas que leen esas hojas (Records y facturación). Se quitan borrándolas, en el orden de `KMV_2.0.md` K2-103.
