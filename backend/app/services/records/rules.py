"""Reglas puras de la hoja hija de Records (SPEC-B18): qué filas crear y qué contexto actualizar."""

from dataclasses import dataclass, field

from app.services.ids.formats import EntityKind, parse_id

TRIGGER = "Records Needed"
KEY = "Master Row"
CONTEXT = (
    "Tracking Project",
    "Customer",
    "Agency",
    "Project Name",
    "Project Address",
    "City",
    "County",
    "Date Received",
)
# Se copian una sola vez al crear la fila (RH-06), si la maestra todavía las tiene.
INITIAL = (
    "Designer2",
    "Request Type",
    "Send Method",
    "Record Request",
    "Reminder Sent",
    "LT Records",
    "Future Project #",
    "PRR #",
    "Security Key",
    "Record Received",
    "Records Status",
    "Record Box",
)

Value = str | bool | None


@dataclass(frozen=True)
class MasterRow:
    row_id: str
    needed: bool
    values: dict[str, Value] = field(default_factory=dict)


@dataclass(frozen=True)
class ChildRow:
    row_id: str
    master: str
    values: dict[str, Value] = field(default_factory=dict)


@dataclass
class Plan:
    create: list[MasterRow] = field(default_factory=list)
    update: list[tuple[str, dict[str, Value]]] = field(default_factory=list)
    waiting: int = 0


def plan(masters: list[MasterRow], children: list[ChildRow]) -> Plan:
    """Una fila por fila marcada con ID canónico; contexto al día (RH-05, RH-07)."""
    linked: dict[str, ChildRow] = {}
    for child in children:
        linked.setdefault(child.master, child)
    result = Plan()
    for master in masters:
        child = linked.get(master.row_id)
        if child is not None:
            changes = {
                title: master.values.get(title)
                for title in CONTEXT
                if _same(master.values.get(title)) != _same(child.values.get(title))
            }
            if changes:
                result.update.append((child.row_id, changes))
        elif master.needed:
            if _has_id(master.values.get("Tracking Project")):
                result.create.append(master)
            else:
                result.waiting += 1
    return result


def _has_id(value: Value) -> bool:
    try:
        parse_id(EntityKind.PROJECT, str(value or "").strip())
    except ValueError:
        return False
    return True


def _same(value: Value) -> Value:
    """Vacío y ausente cuentan igual; el texto se compara sin espacios de los bordes."""
    if isinstance(value, str):
        return value.strip() or None
    return value
