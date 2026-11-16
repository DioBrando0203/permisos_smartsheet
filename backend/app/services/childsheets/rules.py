"""Reglas puras de las hojas hijas (SPEC-B18, SPEC-B19, SPEC-B20): crear y mantener filas."""

from collections.abc import Callable
from dataclasses import dataclass, field

from app.services.ids.formats import EntityKind, parse_id

KEY = "Master Row"
ROW_TYPE = "Row Type"  # calculada por el servicio: madre o hija de la maestra
Value = str | bool | None
# Resumen: misma columna en las dos hojas, o (columna de la hija, columna de la maestra).
Summary = str | tuple[str, str]


@dataclass(frozen=True)
class ChildSpec:
    name: str
    # Columnas de la maestra que piden la fila (casilla marcada o persona asignada; basta una);
    # vacío y sin `when`: toda fila con Tracking Project canónico.
    triggers: tuple[str, ...]
    # Maestra -> hija, siempre al día (bloqueadas en la hija).
    context: tuple[str, ...]
    # Maestra -> hija, una sola vez al crear la fila (si la maestra todavía las tiene).
    initial: tuple[str, ...] = ()
    # Hija -> maestra, siempre al día (sólo si la columna de la maestra no es fórmula).
    summary: tuple[Summary, ...] = ()
    # Calculadas por el servicio a partir de la fila de la maestra.
    derived: tuple[str, ...] = ()
    # Pedido por valor (SPEC-B20 HP-02): recibe los valores de la fila y si es hija.
    when: Callable[[dict[str, Value], bool], bool] | None = None
    # Columnas que lee `when`, además del contexto.
    reads: tuple[str, ...] = ()
    # Vacías en una hija de la maestra: se toman de su proyecto (HP-04).
    fallback: tuple[str, ...] = ()
    # `Row Type` de una madre y de una hija.
    kinds: tuple[str, str] = ("Project", "Permit")
    # El resumen sólo vuelve a hijas de la maestra: la madre conserva su estado (HP-05).
    summary_children_only: bool = False
    # (columna de estado de la hija, valor) que la maestra impone (HP-06): la cancelación.
    cancel: tuple[str, str] | None = None

    @property
    def mirrored(self) -> tuple[str, ...]:
        return (*self.context, *self.derived)

    @property
    def summary_pairs(self) -> tuple[tuple[str, str], ...]:
        """(columna de la hija, columna de la maestra) de cada resumen."""
        return tuple((s, s) if isinstance(s, str) else s for s in self.summary)


@dataclass(frozen=True)
class MasterRow:
    row_id: str
    needed: bool
    values: dict[str, Value] = field(default_factory=dict)
    child: bool = False


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
            back = {}
            if master.child or not spec.summary_children_only:
                back = {
                    theirs: child.values.get(mine)
                    for mine, theirs in spec.summary_pairs
                    if _same(child.values.get(mine)) != _same(master.values.get(theirs))
                }
            _cancel(spec, master, child, changes, back)
            if changes:
                result.update.append((child.row_id, changes))
            if back:
                result.summary.append((master.row_id, back))
        elif master.needed:
            if has_id(master.values.get("Tracking Project")):
                result.create.append(master)
            else:
                result.waiting += 1
    return result


def _cancel(spec: ChildSpec, master: MasterRow, child: ChildRow, changes: dict, back: dict) -> None:
    """Cancelada en la maestra: la hoja de proceso también, y su estado no vuelve encima."""
    if not spec.cancel:
        return
    mine, value = spec.cancel
    theirs = dict(spec.summary_pairs).get(mine, mine)
    if master.values.get(theirs) == value and child.values.get(mine) != value:
        changes[mine] = value
        back.pop(theirs, None)


def with_fallback(
    values: dict[str, Value], project: dict[str, Value], titles: tuple[str, ...]
) -> dict[str, Value]:
    """Valores de una hija con las celdas vacías tomadas de su proyecto (HP-04)."""
    filled = dict(values)
    for title in titles:
        if _same(filled.get(title)) in (None, False):
            filled[title] = project.get(title)
    return filled


def inherit_plan(
    children: list[tuple[str, dict[str, Value], dict[str, Value]]], titles: tuple[str, ...]
) -> list[tuple[str, dict[str, Value]]]:
    """Hijas de la maestra: celdas vacías que su proyecto tiene (HP-07); nunca reemplaza."""
    result = []
    for row_id, mine, project in children:
        missing = {
            title: project[title]
            for title in titles
            if _same(mine.get(title)) in (None, False)
            and _same(project.get(title)) not in (None, False)
        }
        if missing:
            result.append((row_id, missing))
    return result


def _diff(titles: tuple[str, ...], source: dict, target: dict) -> dict[str, Value]:
    return {t: source.get(t) for t in titles if _same(source.get(t)) != _same(target.get(t))}


def has_id(value: Value) -> bool:
    """Tracking Project canónico (con cliente o sólo con año)."""
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
