-- Ejecutar una vez en galp_servicios con el rol administrador; no toca Smartsheet.
BEGIN;
ALTER TABLE auditoria_id DROP CONSTRAINT auditoria_id_accion_check;
ALTER TABLE auditoria_id ADD CONSTRAINT auditoria_id_accion_check
    CHECK (accion IN ('inicializado', 'reservado', 'confirmado'));
GRANT UPDATE (estado) ON asignacion_id TO galp_ids;
COMMIT;
