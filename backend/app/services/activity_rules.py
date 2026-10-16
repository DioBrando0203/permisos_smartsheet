"""Cálculos puros de actividad de una hoja (SPEC-B08): sin E/S.

Trabaja con la última modificación de cada fila; un cambio sobrescrito por otro no se ve.
"""

from collections import defaultdict
from datetime import datetime

from app.models.activity import ActivityEditor, Author, ChangedRow, IdleEditor
from app.services.bulk_plans import PersonLevel
from app.services.permissions import AccessLevel, ShareType, rank
from app.services.smartsheet import RawAuthor, RawRow

LIMITATIONS = [
    "Sólo se ve la última modificación de cada fila: un cambio sobrescrito por otro no aparece.",
    "Borrados de filas y cambios de permisos no se ven: el plan no incluye Event Reporting.",
    "El historial de cada celda se consulta por fila en /rows/{row_id}/history.",
]


# Si una cuenta es la última en tocar más de esta fracción de filas, probablemente es una
# automatización o carga masiva que tapa a los demás editores (sólo queda el último).
DOMINANT_SHARE = 0.8


def dominance_warning(editors: list[ActivityEditor], changed: int) -> str | None:
    """Aviso cuando una cuenta concentra las modificaciones y oculta al resto."""
    if not editors or changed == 0:
        return None
    top = editors[0]
    share = top.rows_changed / changed
    if share <= DOMINANT_SHARE:
        return None
    return (
        f"Una cuenta es la última en modificar el {share:.0%} de las filas del período "
        "(posible automatización o carga masiva): tapa los cambios de los demás, así que "
        "la lista de editores sin cambios no es fiable."
    )


def rows_since(rows: list[RawRow], since: datetime) -> list[RawRow]:
    """Filas modificadas desde `since`, de la más reciente a la más antigua."""
    recent = [row for row in rows if row.modified_at and row.modified_at >= since]
    return sorted(recent, key=lambda row: row.modified_at or since, reverse=True)


def to_changed_row(row: RawRow) -> ChangedRow:
    return ChangedRow(
        row_id=row.id,
        row_number=row.row_number,
        label=row.label,
        created_at=row.created_at,
        created_by=to_author(row.created_by),
        modified_at=row.modified_at,
        modified_by=to_author(row.modified_by),
    )


def editor_stats(recent: list[RawRow], people: dict[str, PersonLevel]) -> list[ActivityEditor]:
    """Quién aparece como último modificador, cuántas filas y su nivel actual en la hoja."""
    grouped: dict[str, list[RawRow]] = defaultdict(list)
    names: dict[str, str | None] = {}
    for row in recent:
        author = row.modified_by
        if author is None or not author.email:
            continue
        grouped[author.email].append(row)
        names.setdefault(author.email, author.name)
    stats = [
        ActivityEditor(
            email=email,
            name=names[email],
            rows_changed=len(rows),
            last_change=max((row.modified_at for row in rows if row.modified_at), default=None),
            access_level=people[email].level if email in people else None,
        )
        for email, rows in grouped.items()
    ]
    return sorted(stats, key=lambda item: (-item.rows_changed, item.email or ""))


def idle_editors(recent: list[RawRow], people: dict[str, PersonLevel]) -> list[IdleEditor]:
    """Con permiso de edición (sin el propietario) y sin filas modificadas en el período."""
    active = {row.modified_by.email for row in recent if row.modified_by}
    idle = [
        IdleEditor(key=key, email=person.email, name=person.name, access_level=person.level)
        for key, person in people.items()
        if person.type is ShareType.USER
        and person.level is not AccessLevel.OWNER
        and rank(person.level) >= rank(AccessLevel.EDITOR)
        and person.email not in active
    ]
    return sorted(idle, key=lambda item: (-rank(item.access_level), item.email or ""))


def to_author(author: RawAuthor | None) -> Author | None:
    return Author(email=author.email, name=author.name) if author else None
