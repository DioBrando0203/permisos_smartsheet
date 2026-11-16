# SPEC-GIS-01 Separación inicial (PEN-55)

- CA-01: el servicio arranca sin token de Smartsheet ni procesador de IDs y sirve el contrato `/api/map` de SPEC-B14.
- CA-02: sus consultas GIS usan las mismas reglas y valores predeterminados que el backend actual; la caché es propia y sólo en memoria.
- CA-03: durante la transición, el panel y el backend existentes siguen atendiendo sus rutas actuales.
- CA-04: las pruebas de arranque y contrato no acceden a fuentes externas.
- Plan: preparar el servicio autónomo; verificar rutas y validaciones; trasladar después la interfaz, configurar su conexión y probar los flujos antes de retirar el código anterior.
- Limitación: hay dos copias temporales; esta etapa no constituye la migración del frontend ni el cambio de tráfico.
