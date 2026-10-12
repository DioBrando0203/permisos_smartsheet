# SPEC-B05 Auditoría, comparación y resumen de acceso

Estado: implementada
Código: `api/routes/reports.py`, `services/reports.py`, `services/audit_rules.py`
Relacionadas: SPEC-B02, SPEC-B03, ADR-B12

## Objetivo

Responder sin tocar nada "¿esta hoja está bien compartida?", "¿qué cambió entre el plan de un año y el del siguiente?" y "¿qué hojas conservan gente que quizá ya no debería estar?".

## Hallazgo que la motivó (2026-10-12, cuenta real)

- Plan Crown Castle 2026: 30 accesos, 17 de correos personales (@hotmail.com) con edición, 2 externos con nivel Administrador, 13 sin nombre.
- Plan 2025 frente a 2026: 24 en común, 5 sólo en 2026 y 3 sólo en 2025.
- Planes 2019 a 2022 con 9 a 16 personas; siguen modificándose, así que la fecha no basta para declararlos inactivos.

## Comportamiento

### Auditoría de una hoja

1. `GET /api/sheets/{sheet_id}/audit` (id o código de permalink).
2. Resumen: total, por nivel, por origen (propio o heredado), por dominio de correo (con marca de dominio personal), externos (no usuarios de la organización), sin nombre, fuera de contactos.
3. Alertas por persona según la tabla de `audit_rules.py` (P-26), cada una con `code`, `severity` (`high`, `medium`, `info`), mensaje y personas afectadas:
   - `EXTERNAL_CAN_SHARE` (high): externo con `ADMIN` o `EDITOR_SHARE`; puede compartir la hoja con cualquiera.
   - `PERSONAL_EMAIL_CAN_EDIT` (medium): dominio personal (hotmail, gmail, outlook, yahoo, live, icloud, etc.) con `EDITOR` o superior.
   - `UNNAMED` (info): sin nombre en Smartsheet; difícil saber quién es.
   - `NOT_IN_CONTACTS` (info): con acceso pero fuera de la libreta.
4. El propietario nunca genera alertas.
5. Si la lista de usuarios de la organización no se puede leer, `org_known=false` y no se emiten alertas de externos.

### Comparar dos hojas

1. `GET /api/sheets/compare?a=&b=` (cada uno id o código de permalink).
2. Por persona o grupo (clave del directorio), con su nivel efectivo en cada hoja (el más alto entre propio y heredado).
3. Respuesta: `only_in_a`, `only_in_b`, `level_differences` (`level_a`, `level_b`) y `same_count`.
4. `a` igual a `b`: 422 `SAME_SHEET`.

### Resumen de acceso por hoja

1. `GET /api/sheets/access-summary?q=&inactive_days=` lee los permisos de las hojas filtradas (caché por hoja).
2. Por hoja: id, nombre, fecha de modificación, `share_count` (sin contar al propietario), `editors_count` (`EDITOR` o superior), `external_count`, `personal_email_count`, `is_inactive` (sólo si se pasa `inactive_days` y la última modificación es más antigua).
3. Orden: `share_count` descendente. Hojas que fallan al leerse: `failed_sheets` (Bulkhead).

## Criterios de aceptación

- CA-01: un externo con `ADMIN` genera `EXTERNAL_CAN_SHARE`; uno de la organización no. Prueba: `test_reports.py::test_audit_flags_external_admin`.
- CA-02: `@hotmail.com` con `EDITOR` genera `PERSONAL_EMAIL_CAN_EDIT`; con `VIEWER` no. Prueba: `test_audit_rules.py::test_personal_email_rule`.
- CA-03: el propietario no genera alertas. Prueba: `test_audit_rules.py::test_owner_is_never_flagged`.
- CA-04: comparar separa sólo en A, sólo en B y diferencias de nivel con el nivel efectivo. Prueba: `test_reports.py::test_compare_sheets`.
- CA-05: comparar una hoja consigo misma: 422 `SAME_SHEET`. Prueba: `test_reports.py::test_compare_same_sheet`.
- CA-06: el resumen cuenta sin el propietario y marca inactivas por días. Prueba: `test_reports.py::test_access_summary`.
- CA-07: ninguna de estas rutas escribe en Smartsheet. Prueba: las anteriores verifican `writes(...) == []`.
- CA-08: lectura real con las hojas de ejemplo. Prueba: manual (RESULTADOS).
