# Vistas de la 2.0 borradas (VA-70 a VA-79)

Historial de las Dynamic Views de la 2.0 que se borraron a pedido del usuario, con lo que tenían al borrarse (leído en la aplicación de Dynamic View antes de borrar, sólo lectura). Regla general: no se borra ninguna vista de la 2.0 sin pedido expreso del usuario (README VA-09).

## VA-70 `KMV 2.0 | Records`

- Id `e3e5b9e2-6d18-44ef-8fb5-0c118f209ed4`. Borrada el 2026-11-23 a pedido del usuario ("si sólo necesitamos uno, borra uno").
- Origen: reporte `KMV 2.0 | Records` (`8810630590189444`, carpeta `PROJECT KMV 2.0 - Prototype/Reports`), de cuando las vistas de la 2.0 se armaban sobre reportes (antes de la regla K2-60: cada vista sobre su hoja).
- Restricción por usuario: `Records Owner`. Sin filtro de hoja.
- Tabla y panel: vacíos (sin columnas configuradas); sin reglas de `Field Logic`.
- Sin compartir (sólo la veía la cuenta dueña) y ningún aviso de las 36 hojas de Pruebas la enlazaba.
- Reemplazo: `PROJECT KMV 2.0 - RECORDS` (`b53989d4-0e44-4aab-8bc3-a8e763aab856`), sobre la hoja `Records Requests (Prototype)` (`../VISTAS_KMV_2.0.md` VK-36 a VK-39). El reporte se quedó, de consulta.
