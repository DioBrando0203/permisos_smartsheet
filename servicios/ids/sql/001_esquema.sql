-- Esquema inicial para el servicio futuro de IDs; no accede a Smartsheet.
-- Ejecutar una sola vez en una base vacía y dedicada.
BEGIN;

CREATE TABLE secuencia_id (
    ambito text PRIMARY KEY CHECK (length(trim(ambito)) > 0),
    ultimo_numero bigint NOT NULL CHECK (ultimo_numero >= 0)
);

CREATE TABLE asignacion_id (
    hoja_id bigint NOT NULL CHECK (hoja_id > 0),
    fila_id bigint NOT NULL CHECK (fila_id > 0),
    ambito text NOT NULL REFERENCES secuencia_id (ambito),
    numero bigint NOT NULL CHECK (numero > 0),
    id_generado text NOT NULL CHECK (length(trim(id_generado)) > 0),
    estado text NOT NULL CHECK (estado IN ('reservado', 'confirmado')),
    PRIMARY KEY (hoja_id, fila_id),
    UNIQUE (ambito, numero),
    UNIQUE (id_generado)
);

COMMIT;
