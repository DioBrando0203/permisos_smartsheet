# SPEC-B06 Operaciones masivas: copiar permisos y quitar accesos en bloque

Estado: implementada; ejecución real bloqueada por `APP_READ_ONLY=true` y sin verificar (PEN-07)
Código: `api/routes/bulk.py`, `services/bulk.py`, `services/bulk_plans.py`
Relacionadas: SPEC-B02, SPEC-B05, ADR-B11, ADR-B13, PEN-11

## Objetivo

Preparar el plan del año siguiente con el mismo equipo y retirar a una persona de muchas hojas, viendo antes exactamente qué se haría.

## Principios (ADR-B13)

- Simulación por defecto: `dry_run` es `true` si no se envía. La simulación nunca escribe y funciona en modo solo lectura.
- Ejecutar exige `dry_run=false` y `APP_READ_ONLY=false`; si no, 403 `READ_ONLY_MODE`.
- Copiar sólo agrega o sube niveles: nunca baja ni quita a nadie en la hoja destino.
- Cada paso se ejecuta aislado: uno que falla no detiene el resto y se informa con su código.
- Mismas reglas de SPEC-B02: propietario y heredados no se tocan; `OWNER` nunca se asigna.

## Comportamiento

### Copiar permisos de una hoja a otra

1. `POST /api/sheets/{sheet_id}/shares/copy` con `{source_sheet_id, upgrade_levels: false, include_inherited: false, dry_run: true}`. `{sheet_id}` es la hoja destino.
2. Origen: permisos propios de la hoja origen (y heredados si `include_inherited`), con su nivel. `OWNER` se copia como `ADMIN` (no transfiere propiedad).
3. Plan por persona: `create` (no está en destino), `upgrade` (está con nivel menor y `upgrade_levels=true`), `keep` (igual o mayor, o menor sin `upgrade_levels`), `skip` (en destino es propietario o heredado).
4. Con `dry_run=false`: crea agrupando por nivel (sin correo de aviso) y sube niveles uno a uno; cada paso con `status` `done` o `failed` y `code`.
5. Respuesta `CopyPlan`: `source`, `target`, `dry_run`, `steps[]` y conteos por acción.

### Quitar a una persona de varias hojas

1. `POST /api/users/{key}/revoke` con `{sheet_ids: null | [...], dry_run: true}`. Sin `sheet_ids`, todas las hojas donde tiene acceso.
2. Plan por hoja: `remove` (permiso propio editable) o `skip` con `locked_reason` (propietario, heredado, sin permiso).
3. Con `dry_run=false`: borra cada permiso `remove`; resultado por hoja.
4. Respuesta `RevokePlan`: `person`, `dry_run`, `steps[]`, conteos.

## Criterios de aceptación

- CA-01: copiar en simulación lista `create`, `keep`, `upgrade` y `skip` sin escribir. Prueba: `test_bulk.py::test_copy_plan_dry_run`.
- CA-02: `OWNER` de origen se planifica como `ADMIN`. Prueba: `test_bulk_plans.py::test_owner_is_copied_as_admin`.
- CA-03: sin `upgrade_levels`, un nivel menor en destino queda `keep`; nunca hay bajadas. Prueba: `test_bulk_plans.py::test_copy_never_downgrades`.
- CA-04: ejecutar en modo solo lectura: 403 `READ_ONLY_MODE` y ninguna escritura. Prueba: `test_bulk.py::test_execute_blocked_in_read_only`.
- CA-05: ejecutar copia agrupa altas por nivel con `sendEmail=false` y un fallo no detiene el resto. Prueba: `test_bulk.py::test_copy_execute_isolates_failures`.
- CA-06: revocar en simulación separa `remove` y `skip` (heredado). Prueba: `test_bulk.py::test_revoke_plan`.
- CA-07: revocar ejecutado borra sólo los `remove`. Prueba: `test_bulk.py::test_revoke_execute`.
- CA-08: simulaciones reales con las hojas de ejemplo (2025 a 2026). Prueba: manual (RESULTADOS).
