-- Ejecutar una vez en galp_servicios con el rol administrador; no toca Smartsheet.
-- Comentarios ya copiados a la columna Obs (SPEC-B17 OB-05): sólo estado técnico.
BEGIN;
CREATE TABLE IF NOT EXISTS obs_comentario (
    comentario_id bigint PRIMARY KEY,
    hoja_id bigint NOT NULL,
    fila_id bigint NOT NULL,
    incorporado timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS obs_comentario_hoja ON obs_comentario (hoja_id);
GRANT SELECT, INSERT ON obs_comentario TO galp_ids;
COMMIT;
