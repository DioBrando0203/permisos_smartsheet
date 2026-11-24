"""Comentarios ya copiados a Obs, en PostgreSQL (migración 004): sólo estado técnico."""

import psycopg


class ObsStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def processed(self, sheet_id: str) -> set[str]:
        with psycopg.connect(self.dsn, connect_timeout=5) as conn:
            rows = conn.execute(
                "SELECT comentario_id FROM obs_comentario WHERE hoja_id = %s", (int(sheet_id),)
            ).fetchall()
        return {str(row[0]) for row in rows}

    def record(self, comments: list[tuple[str, str, str]]) -> None:
        """(hoja, fila, comentario) de cada comentario incorporado, en una sola transacción.

        La hoja y la fila son donde está el comentario: la maestra o una hoja de equipo
        (SPEC-B17 OB-17). Idempotente: un comentario ya registrado se ignora.
        """
        if not comments:
            return
        with psycopg.connect(self.dsn, connect_timeout=5) as conn:
            conn.cursor().executemany(
                "INSERT INTO obs_comentario (comentario_id, hoja_id, fila_id) "
                "VALUES (%s, %s, %s) ON CONFLICT (comentario_id) DO NOTHING",
                [(int(comment), int(sheet), int(row)) for sheet, row, comment in comments],
            )
