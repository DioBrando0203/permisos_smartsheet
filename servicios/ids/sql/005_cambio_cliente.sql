-- Ejecutar una vez en galp_servicios con el rol administrador; no toca Smartsheet.
-- Cambio de cliente (SPEC-ID01 ID-44): el ID anterior de la fila se retira y nunca se reutiliza.
BEGIN;
CREATE TABLE IF NOT EXISTS id_retirado (
    id_generado text PRIMARY KEY,
    hoja_id bigint NOT NULL,
    fila_id bigint NOT NULL,
    ambito text NOT NULL,
    numero bigint NOT NULL,
    motivo text NOT NULL,
    retirado timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE auditoria_id DROP CONSTRAINT IF EXISTS auditoria_id_accion_check;
ALTER TABLE auditoria_id ADD CONSTRAINT auditoria_id_accion_check
    CHECK (accion IN ('inicializado', 'reservado', 'confirmado', 'retirado'));
GRANT SELECT, INSERT ON id_retirado TO galp_ids;
GRANT DELETE ON asignacion_id TO galp_ids;
COMMIT;
