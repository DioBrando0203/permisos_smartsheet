# Plan de calidad (backend)

Reglas en `reglas_calidad/REGLAS.md`. Última ejecución en `RESULTADOS.md`.

## Mapa de pruebas

- `tests/conftest.py`: `make_settings` (token ficticio, sin esperas entre reintentos, escritura habilitada), `smartsheet` (respx con rutas por defecto; una solicitud no simulada falla), `make_client` y `client` (`httpx.AsyncClient` con `ASGITransport`), `writes` (escrituras que llegaron a Smartsheet simulado).
- `tests/factories.py`: JSON sintético de Smartsheet con correos `@example.com`.
- `test_client.py`: cabecera con token y logs sin token, 429 con reintentos, 500 reintentado en lectura y no en escritura, `lastKey`, 401 traducido, token ausente.
- `test_shares.py`: SPEC-B02 completa: bloqueos, solo lectura, propietario, heredado, duplicados, omitidos, sin correo por defecto, cuerpos y query enviados, no-op, invalidación de caché, ids inválidos.
- `test_people.py`: SPEC-B03 y búsqueda de SPEC-B01.
- `test_permissions.py`: reglas para todos los niveles y scopes, orden, duplicados, caché (vencimiento, single flight, invalidación).
- `test_audit_rules.py`: reglas de auditoría (personales, externos, propietario, duplicados) y planes de copia (OWNER a ADMIN, sin bajadas, heredados, origen heredado).
- `test_reports.py`: SPEC-B05: auditoría, comparación, misma hoja, resumen de acceso.
- `test_bulk.py`: SPEC-B06: simulación, bloqueo en solo lectura, ejecución con fallo aislado y `sendEmail=false`, revocar simulado y ejecutado.
- `test_review.py`: SPEC-B07: agregación por hoja y persona, filtro de severidad, hoja fallida.
- `test_launcher.py`: puerto preferido libre, respaldo a uno libre, orígenes del puerto real, `.port` sólo lo borra su dueño y cierre ordenado del proceso.
- `test_activity.py`: SPEC-B08: período, editores con nivel actual, paginación de filas, historial de fila con columna fallida, columna inexistente.
- `test_activity_rules.py`: período, editores sin cambios, conteo por editor y aviso de cuenta dominante.
- `test_org_sheets.py`: hojas de la organización marcadas, sólo consulta y respaldo si se niega `/users/sheets`.
- `test_quality_rules.py` y `test_quality.py`: repetidos, vacíos, formato, errores de columna y de expresión, columnas pedidas, listado de columnas.
- `test_export.py`: CSV para Excel (BOM, `;`, fórmulas neutralizadas, columnas en español).
- `test_automation_rules.py` y `test_automations.py`: cada problema de la tabla, regla sana, vista por hoja y de cuenta con hoja fallida.
- `test_references.py`: referencias por hoja (catálogo por permalink) y de cuenta (sin catálogo, hojas sin la columna, faltantes por valor sin distinguir mayúsculas).
- `test_workload_rules.py` y `test_designers.py`: estado y fase, mismo diseñador en dos columnas, encabezados copiados, persona por nombre, acceso por hoja y estados cerrados configurables.
- `test_frontend.py`: build servido, rutas del panel a `index.html`, API y `/docs` intactos, sin salir de `dist`, sin build no se monta nada.
- `tests/fake_data.py` y `tests/fake_smartsheet.py`: Smartsheet falso con datos sintéticos que registra escrituras (ADR-10 del frontend); `python -m tests.fake_smartsheet --port 8791`.
- `test_fake_smartsheet.py`: el backend completo contra el falso (lecturas, reportes, calidad, diseñadores, CSV y escrituras registradas); si falla, el falso dejó de parecerse a Smartsheet.
- `tests/fake_gis_data.py` y `tests/fake_gis.py`: GIS falso (capas ArcGIS del FDOT y de FDACS, geocodificador del Censo) con la vía sintética del caso de control; filtra por radio, campos, geometría y medida M como el real y anota si alguna solicitud llevó `Authorization`; `python -m tests.fake_gis --port 8792`.
- `test_trace_rules.py` (reglas puras del trazo con dos vías sintéticas que se cruzan), `test_map_rules.py` (longitud de LineString LRS) y `test_map_trace.py` (Turnpike, validación sin consultar fuentes, sin vías, capa 8 caída, longitudes manual/oficial y ajustes de extremos) (PEN-32, PEN-35, PEN-36).
- `test_map_fallback.py`: fuente que no conecta (un solo intento, pausa y vuelta a intentar) y respaldo de parcelas de Broward sólo cuando FDACS falla en Broward (PEN-30).
- `test_fake_gis.py`: el backend completo contra el GIS falso (punto sobre la vía y fuera de ella, tramo con `osp_row`, buscador por ruta, calle y dirección, trazo con la fila de OSP y contornos de Miami-Dade).
- `tests/e2e_backend.py` y `test_e2e_backend.py`: backend real para el E2E del frontend, apuntado a los dos falsos, en solo lectura y sin tomar token ni URL de `.env` ni del entorno.
- `test_security.py`: un solo grupo de Swagger por endpoint; httpx sin URLs en el log, Origin, Host, salud sin llamadas, token secreto, solo lectura por defecto, listas del entorno.

## Comandos

Desde `backend/`:

- `.venv/bin/python -m pytest` (Windows: `.venv/Scripts/python.exe`).
- `.venv/bin/python -m ruff check app tests`.
- `.venv/bin/python -m ruff format --check app tests`.

## Verificación manual con la cuenta real

- Lecturas: levantar con `--env-file .env`, abrir `/docs` y ejecutar `GET /api/me`, `/api/sheets`, `/api/sheets/{id}/shares`, `/api/users`. Anotar cantidades y tiempos en RESULTADOS, sin nombres ni correos.
- Escrituras: sólo en la hoja y con el correo de prueba que designe el usuario (PEN-07). Orden: crear, cambiar, quitar; confirmar en Smartsheet que quedó como al inicio.

## Cuándo ampliar

- Endpoint nuevo de Smartsheet: éxito, 404, 429 y 5xx.
- Regla nueva de permisos: todos los niveles y scopes (QB-05).
- Cambio de contrato: actualizar `estilos/API.md` y, si existe, los tipos del frontend.
