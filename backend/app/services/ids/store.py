"""Reservas transaccionales de PostgreSQL; no consulta ni modifica Smartsheet."""

from dataclasses import dataclass

import psycopg

from app.services.ids.formats import EntityKind, make_id, parse_id
from app.services.ids.transition import standard_start

_INIT_LOCK = 714382001


@dataclass(frozen=True)
class ExistingId:
    sheet_id: int
    row_id: int
    kind: EntityKind
    value: str


@dataclass(frozen=True)
class Reservation:
    value: str
    state: str


class IdStore:
    """Crea transacciones por operación, con una conexión independiente por llamada."""

    def __init__(
        self,
        dsn: str,
        *,
        allow_reservations: bool = False,
        approved_starts: dict[str, int] | None = None,
        annual_policy_approved: bool = False,
    ) -> None:
        self._dsn = dsn
        self._allow_reservations = allow_reservations
        self._approved_starts = dict(approved_starts or {})
        self._annual_policy_approved = annual_policy_approved

    def lookup(self, sheet_id: int, row_id: int) -> Reservation | None:
        """Consulta la reserva de una fila sin modificarla."""
        with psycopg.connect(self._dsn) as conn:
            row = conn.execute(
                "SELECT id_generado, estado FROM asignacion_id WHERE hoja_id=%s AND fila_id=%s",
                (sheet_id, row_id),
            ).fetchone()
            return Reservation(*row) if row else None

    def confirmed_parent(self, sheet_id: int, value: str) -> int | None:
        """Encuentra la fila confirmada del padre dentro de su hoja autorizada."""
        with psycopg.connect(self._dsn) as conn:
            row = conn.execute(
                "SELECT fila_id FROM asignacion_id WHERE hoja_id=%s AND id_generado=%s "
                "AND estado='confirmado'",
                (sheet_id, value),
            ).fetchone()
            return row[0] if row else None

    def is_service_reservation(self, sheet_id: int, row_id: int) -> bool:
        """Distingue una reserva propia de un ID importado anteriormente."""
        with psycopg.connect(self._dsn) as conn:
            return bool(
                conn.execute(
                    "SELECT 1 FROM auditoria_id WHERE hoja_id=%s AND fila_id=%s "
                    "AND accion='reservado' LIMIT 1",
                    (sheet_id, row_id),
                ).fetchone()
            )

    def lock_sheet(self, sheet_id: int) -> psycopg.Connection | None:
        """Impide dos escritores del servicio sobre la misma hoja."""
        conn = psycopg.connect(self._dsn, autocommit=True, connect_timeout=5)
        if not conn.execute(
            "SELECT pg_try_advisory_lock(%s, %s)", (714382, sheet_id % 2147483647)
        ).fetchone()[0]:
            conn.close()
            return None
        return conn

    def initialize(
        self, entries: list[ExistingId], historical: list[tuple[EntityKind, str]] | None = None
    ) -> None:
        """Carga el inventario completo; una repetición idéntica no altera datos."""
        if not entries:
            raise ValueError("El inventario no puede estar vacío")
        rows = {(entry.sheet_id, entry.row_id) for entry in entries}
        values = {entry.value for entry in entries}
        if len(rows) != len(entries) or len(values) != len(entries):
            raise ValueError("El inventario contiene duplicados")
        with psycopg.connect(self._dsn) as conn:
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (_INIT_LOCK,))
            if conn.execute("SELECT 1 FROM estado_inicializacion_id").fetchone():
                self._check_existing(conn, entries, historical or [])
                return
            if conn.execute("SELECT 1 FROM asignacion_id LIMIT 1").fetchone():
                raise ValueError("Ya existen asignaciones; requiere reconciliación")
            for kind, value in historical or []:
                parts = parse_id(kind, value)
                self._advance(conn, parts.scope, parts.number)
            for entry in entries:
                parts = parse_id(entry.kind, entry.value)
                self._advance(conn, parts.scope, parts.number)
                conn.execute(
                    "INSERT INTO asignacion_id VALUES (%s, %s, %s, %s, %s, 'confirmado')",
                    (entry.sheet_id, entry.row_id, parts.scope, parts.number, entry.value),
                )
                self._audit(conn, "inicializado", entry.sheet_id, entry.row_id, entry.value)
            conn.execute("INSERT INTO estado_inicializacion_id DEFAULT VALUES")

    @staticmethod
    def _check_existing(
        conn: psycopg.Connection,
        entries: list[ExistingId],
        historical: list[tuple[EntityKind, str]],
    ) -> None:
        imported = set(
            conn.execute(
                "SELECT hoja_id, fila_id FROM asignacion_id WHERE estado='confirmado'"
            ).fetchall()
        )
        if imported != {(entry.sheet_id, entry.row_id) for entry in entries}:
            raise ValueError("Inventario incompleto o cambiado; requiere reconciliación")
        for entry in entries:
            parts = parse_id(entry.kind, entry.value)
            existing = conn.execute(
                "SELECT ambito, numero, id_generado, estado FROM asignacion_id "
                "WHERE hoja_id=%s AND fila_id=%s",
                (entry.sheet_id, entry.row_id),
            ).fetchone()
            if existing != (parts.scope, parts.number, entry.value, "confirmado"):
                raise ValueError("Inventario distinto; requiere reconciliación")
        for kind, value in historical:
            parts = parse_id(kind, value)
            sequence = conn.execute(
                "SELECT ultimo_numero FROM secuencia_id WHERE ambito=%s", (parts.scope,)
            ).fetchone()
            if not sequence or sequence[0] < parts.number:
                raise ValueError("Máximo histórico no incorporado; requiere reconciliación")

    def reserve(
        self,
        sheet_id: int,
        row_id: int,
        kind: EntityKind,
        parent: str,
        preferred: int | None = None,
    ) -> Reservation:
        """Reserva sin reutilizar números; la misma fila y ámbito devuelve la misma reserva.

        `preferred` es el número de la fórmula: se adopta si supera el máximo registrado; si no,
        se usa el siguiente libre. Nunca baja del máximo ni repite un número.
        """
        if not self._allow_reservations:
            raise ValueError("Reservas deshabilitadas hasta resolver los máximos históricos")
        make_id(kind, parent, 1)
        scope = f"{kind.value}:{parent}"
        with psycopg.connect(self._dsn) as conn:
            conn.execute("SELECT pg_advisory_xact_lock_shared(%s)", (_INIT_LOCK,))
            if not conn.execute("SELECT 1 FROM estado_inicializacion_id").fetchone():
                raise ValueError("Debe inicializar el inventario antes de reservar")
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"{sheet_id}:{row_id}",)
            )
            existing = conn.execute(
                "SELECT ambito, id_generado, estado FROM asignacion_id "
                "WHERE hoja_id=%s AND fila_id=%s",
                (sheet_id, row_id),
            ).fetchone()
            if existing:
                if existing[0] != scope:
                    raise ValueError("La fila ya tiene un ID en otro ámbito")
                return Reservation(existing[1], existing[2])
            # Un inicio aprobado explícito prevalece; si no, la política crea el ámbito desde 1.
            start = self._approved_starts.get(scope)
            if start is None and self._annual_policy_approved:
                start = standard_start(kind, parent)
            if not isinstance(start, int) or isinstance(start, bool) or start < 1:
                raise ValueError("Falta consecutivo inicial aprobado para este ámbito")
            first = preferred if isinstance(preferred, int) and preferred >= start else start
            number = conn.execute(
                "INSERT INTO secuencia_id VALUES (%s, %s) ON CONFLICT (ambito) "
                "DO UPDATE SET ultimo_numero=GREATEST(secuencia_id.ultimo_numero+1, "
                "EXCLUDED.ultimo_numero) RETURNING ultimo_numero",
                (scope, first),
            ).fetchone()[0]
            value = make_id(kind, parent, number)
            conn.execute(
                "INSERT INTO asignacion_id VALUES (%s, %s, %s, %s, %s, 'reservado')",
                (sheet_id, row_id, scope, number, value),
            )
            self._audit(conn, "reservado", sheet_id, row_id, value)
            return Reservation(value, "reservado")

    def register_existing(
        self, sheet_id: int, row_id: int, kind: EntityKind, value: str
    ) -> Reservation:
        """Registra un Stable ID que ya está en la hoja sin rastro en PostgreSQL; nunca lo cambia.

        Rechaza el valor si su ID o su número ya pertenecen a otra fila.
        """
        if not self._allow_reservations:
            raise ValueError("Registro deshabilitado sin escritura aprobada")
        parts = parse_id(kind, value)
        with psycopg.connect(self._dsn) as conn:
            conn.execute("SELECT pg_advisory_xact_lock_shared(%s)", (_INIT_LOCK,))
            if not conn.execute("SELECT 1 FROM estado_inicializacion_id").fetchone():
                raise ValueError("Debe inicializar el inventario antes de registrar")
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"{sheet_id}:{row_id}",)
            )
            existing = conn.execute(
                "SELECT id_generado, estado FROM asignacion_id WHERE hoja_id=%s AND fila_id=%s",
                (sheet_id, row_id),
            ).fetchone()
            if existing:
                if existing[0] != value:
                    raise ValueError("La fila ya tiene otro ID registrado")
                return Reservation(*existing)
            if conn.execute("SELECT 1 FROM id_retirado WHERE id_generado=%s", (value,)).fetchone():
                raise ValueError("El Stable ID fue retirado y no se reutiliza")
            self._advance(conn, parts.scope, parts.number)
            try:
                conn.execute(
                    "INSERT INTO asignacion_id VALUES (%s, %s, %s, %s, %s, 'confirmado')",
                    (sheet_id, row_id, parts.scope, parts.number, value),
                )
            except psycopg.errors.UniqueViolation:
                raise ValueError("El Stable ID ya pertenece a otra fila") from None
            self._audit(conn, "inicializado", sheet_id, row_id, value)
            return Reservation(value, "confirmado")

    def confirm(self, sheet_id: int, row_id: int, value: str) -> None:
        """Confirma una reserva coincidente y audita una sola vez; no consulta Smartsheet."""
        with psycopg.connect(self._dsn) as conn:
            row = conn.execute(
                "SELECT id_generado, estado FROM asignacion_id "
                "WHERE hoja_id=%s AND fila_id=%s FOR UPDATE",
                (sheet_id, row_id),
            ).fetchone()
            if not row or row[0] != value:
                raise ValueError("Reserva inexistente o diferente")
            if row[1] == "confirmado":
                return
            conn.execute(
                "UPDATE asignacion_id SET estado='confirmado' WHERE hoja_id=%s AND fila_id=%s",
                (sheet_id, row_id),
            )
            self._audit(conn, "confirmado", sheet_id, row_id, value)

    def retire(self, sheet_id: int, row_id: int, value: str, reason: str) -> None:
        """Retira el ID de una fila (cambio de cliente): queda en `id_retirado`, nunca vuelve."""
        if not self._allow_reservations:
            raise ValueError("Retiro deshabilitado sin escritura aprobada")
        with psycopg.connect(self._dsn) as conn:
            row = conn.execute(
                "SELECT ambito, numero, id_generado FROM asignacion_id "
                "WHERE hoja_id=%s AND fila_id=%s FOR UPDATE",
                (sheet_id, row_id),
            ).fetchone()
            if not row or row[2] != value:
                raise ValueError("Asignación inexistente o diferente")
            conn.execute(
                "INSERT INTO id_retirado (id_generado, hoja_id, fila_id, ambito, numero, motivo) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (value, sheet_id, row_id, row[0], row[1], reason),
            )
            conn.execute(
                "DELETE FROM asignacion_id WHERE hoja_id=%s AND fila_id=%s", (sheet_id, row_id)
            )
            self._audit(conn, "retirado", sheet_id, row_id, value)

    @staticmethod
    def _advance(conn: psycopg.Connection, scope: str, number: int) -> None:
        conn.execute(
            "INSERT INTO secuencia_id VALUES (%s, %s) ON CONFLICT (ambito) "
            "DO UPDATE SET ultimo_numero = "
            "GREATEST(secuencia_id.ultimo_numero, EXCLUDED.ultimo_numero)",
            (scope, number),
        )

    @staticmethod
    def _audit(
        conn: psycopg.Connection, action: str, sheet_id: int, row_id: int, value: str
    ) -> None:
        conn.execute(
            "INSERT INTO auditoria_id (accion, hoja_id, fila_id, id_generado) VALUES (%s,%s,%s,%s)",
            (action, sheet_id, row_id, value),
        )
