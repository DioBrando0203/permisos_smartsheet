# Reglas de calidad (backend)

- QB-01: todo cambio de comportamiento trae una prueba que falla sin el cambio.
- QB-02: la suite nunca llama a Smartsheet. `respx` simula `httpx`; una solicitud no simulada debe hacer fallar la prueba (`assert_all_mocked=True`).
- QB-03: fixtures sólo sintéticos (`tests/factories.py`): correos `@example.com`, nombres inventados, ids de 16 dígitos inventados. Nunca copiar respuestas reales de la cuenta.
- QB-04: cada ruta se prueba en éxito, error de Smartsheet traducido y validación de entrada.
- QB-05: cada regla de `permissions/` se prueba con todos los niveles y los dos `scope`.
- QB-06: las escrituras se prueban verificando el método, la ruta, la query (`assetType`, `assetId`, `sendEmail`) y el cuerpo enviados a Smartsheet.
- QB-07: las pruebas de protección (propietario, heredado, Origin) verifican además que no hubo ninguna llamada de escritura a Smartsheet.
- QB-08: refactorizaciones sin cambio de comportamiento se validan con la suite completa sin modificar aserciones.
- QB-09: verificación real: lecturas contra la cuenta cuando cambia un mapeo; escrituras sólo en la hoja de prueba (PEN-07), revertidas y anotadas.
- QB-10: resultados en `calidad/RESULTADOS.md` sólo de ejecuciones reales, con entorno y hora de Lima.
