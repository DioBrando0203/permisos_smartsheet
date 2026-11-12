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

    def record(self, sheet_id: str, row_id: str, comment_ids: list[str]) -> None:
        """Idempotente: un comentario ya registrado se ignora."""
        if not comment_ids:
            return
        with psycopg.connect(self.dsn, connect_timeout=5) as conn:
            conn.cursor().executemany(
                "INSERT INTO obs_comentario (comentario_id, hoja_id, fila_id) "
                "VALUES (%s, %s, %s) ON CONFLICT (comentario_id) DO NOTHING",
                [(int(item), int(sheet_id), int(row_id)) for item in comment_ids],
            )
