-- Ejecutar una vez sobre el esquema 001; no modifica datos de Smartsheet.
BEGIN;

CREATE TABLE estado_inicializacion_id (
    unico boolean PRIMARY KEY DEFAULT true CHECK (unico),
    inicializado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auditoria_id (
    evento_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha timestamptz NOT NULL DEFAULT now(),
    accion text NOT NULL CHECK (accion IN ('inicializado', 'reservado')),
    hoja_id bigint,
    fila_id bigint,
    id_generado text
);

COMMIT;
