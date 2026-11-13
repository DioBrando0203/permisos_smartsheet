"""Reglas puras de las hojas hijas (SPEC-B18, SPEC-B19): crear y mantener contexto y resumen."""

from dataclasses import dataclass, field

from app.services.ids.formats import EntityKind, parse_id

KEY = "Master Row"
ROW_TYPE = "Row Type"  # calculada por el servicio: madre o hija de la maestra
Value = str | bool | None


@dataclass(frozen=True)
class ChildSpec:
    name: str
    # Casilla de la maestra que pide la fila; None: toda fila con Tracking Project canónico.
    trigger: str | None
    # Maestra -> hija, siempre al día (bloqueadas en la hija).
    context: tuple[str, ...]
    # Maestra -> hija, una sola vez al crear la fila (si la maestra todavía las tiene).
    initial: tuple[str, ...] = ()
    # Hija -> maestra, siempre al día (sólo si la columna de la maestra no es fórmula).
    summary: tuple[str, ...] = ()
    # Calculadas por el servicio a partir de la fila de la maestra.
    derived: tuple[str, ...] = ()

    @property
    def mirrored(self) -> tuple[str, ...]:
        return (*self.context, *self.derived)


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
    summary: list[tuple[str, dict[str, Value]]] = field(default_factory=list)
    waiting: int = 0


def plan(spec: ChildSpec, masters: list[MasterRow], children: list[ChildRow]) -> Plan:
    """Una fila hija por fila pedida con ID; contexto y resumen al día; nunca borra."""
    linked: dict[str, ChildRow] = {}
    for child in children:
        linked.setdefault(child.master, child)
    result = Plan()
    for master in masters:
        child = linked.get(master.row_id)
        if child is not None:
            changes = _diff(spec.mirrored, master.values, child.values)
            if changes:
                result.update.append((child.row_id, changes))
            back = _diff(spec.summary, child.values, master.values)
            if back:
                result.summary.append((master.row_id, back))
        elif master.needed:
            if _has_id(master.values.get("Tracking Project")):
                result.create.append(master)
            else:
                result.waiting += 1
    return result


def _diff(titles: tuple[str, ...], source: dict, target: dict) -> dict[str, Value]:
    return {t: source.get(t) for t in titles if _same(source.get(t)) != _same(target.get(t))}


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
