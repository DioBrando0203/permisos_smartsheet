"""Catálogo de proyectos y clasificación de Linked Tracking; reglas puras sin acceso a datos."""

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from app.services.ids.formats import EntityKind, parse_id


class Origin(StrEnum):
    CURRENT = "current"  # proyecto del piloto con Stable ID permanente
    HISTORICAL = "historical"  # referencia conocida que no está cargada en el piloto


class LinkStatus(StrEnum):
    EMPTY = "empty"  # Linked Tracking es opcional
    CURRENT_VALID = "current_valid"
    HISTORICAL_VALID = "historical_valid"
    UNVERIFIABLE = "unverifiable"  # mismo cliente, pero sin origen comprobable todavía
    OTHER_CUSTOMER = "other_customer"
    SAME_PROJECT = "same_project"
    INVALID = "invalid"  # no tiene formato de proyecto


VALID = frozenset({LinkStatus.EMPTY, LinkStatus.CURRENT_VALID, LinkStatus.HISTORICAL_VALID})


@dataclass(frozen=True)
class ProjectRow:
    """Fila mínima de Proyectos: sólo las columnas que necesita el catálogo."""

    row_id: str
    row_number: int | None
    stable: str
    visible: str
    customer: str
    customer_code: str
    company: str
    linked: str


@dataclass(frozen=True)
class CatalogEntry:
    tracking_project: str
    company: str
    customer_code: str
    customer: str
    origin: Origin
    row_id: str | None = None


def id_parts(value: str) -> tuple[str, str]:
    """Empresa y código de cliente de un ID de proyecto canónico; ValueError si no lo es."""
    company, customer_code, _year = parse_id(EntityKind.PROJECT, value.strip()).parent.split("-")
    return company, customer_code


def customer_name(code: str, options: tuple[str, ...]) -> str:
    """Nombre del desplegable Customer para un código (`CC` -> `CC-Crown Castle`)."""
    return next((option for option in options if option.split("-", 1)[0] == code), "")


def build_catalog(
    rows: list[ProjectRow], known: list[str], customers: tuple[str, ...]
) -> tuple[list[CatalogEntry], list[str]]:
    """Proyectos actuales (con Stable ID) más históricos conocidos; devuelve también duplicados.

    `known` son referencias curadas (opciones del desplegable o filas históricas del catálogo).
    Un histórico nunca reemplaza a un proyecto actual con el mismo ID.
    """
    counts = Counter(row.stable for row in rows if row.stable)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    entries: dict[str, CatalogEntry] = {}
    for row in rows:
        if not row.stable or row.stable in entries:
            continue
        try:
            company, code = id_parts(row.stable)
        except ValueError:
            continue
        entries[row.stable] = CatalogEntry(
            row.stable,
            row.company or company,
            row.customer_code or code,
            row.customer or customer_name(code, customers),
            Origin.CURRENT,
            row.row_id,
        )
    for value in known:
        value = value.strip()
        if value in entries:
            continue
        try:
            company, code = id_parts(value)
        except ValueError:
            continue
        entries[value] = CatalogEntry(
            value, company, code, customer_name(code, customers), Origin.HISTORICAL
        )
    return sorted(entries.values(), key=_order), duplicates


def classify_link(row: ProjectRow, catalog: dict[str, CatalogEntry]) -> LinkStatus:
    """Clasifica sin corregir: un histórico ausente del catálogo no es un error."""
    linked = row.linked.strip()
    if not linked:
        return LinkStatus.EMPTY
    if linked in (row.stable, row.visible):
        return LinkStatus.SAME_PROJECT
    try:
        _company, code = id_parts(linked)
    except ValueError:
        return LinkStatus.INVALID
    entry = catalog.get(linked)
    if not row.customer_code:
        return LinkStatus.UNVERIFIABLE
    if (entry.customer_code if entry else code) != row.customer_code:
        return LinkStatus.OTHER_CUSTOMER
    if entry is None:
        return LinkStatus.UNVERIFIABLE
    if entry.origin == Origin.CURRENT:
        return LinkStatus.CURRENT_VALID
    return LinkStatus.HISTORICAL_VALID


def filter_catalog(
    entries: list[CatalogEntry], customer_code: str | None, company: str | None
) -> list[CatalogEntry]:
    """Proyectos de un cliente y, si se indica, de una empresa; sin distinguir mayúsculas."""
    code = (customer_code or "").strip().upper()
    firm = (company or "").strip().upper()
    return [
        entry
        for entry in entries
        if (not code or entry.customer_code.upper() == code)
        and (not firm or entry.company.upper() == firm)
    ]


def _order(entry: CatalogEntry) -> tuple[str, str, str]:
    # Agrupa por cliente y empresa: así el desplegable vinculado muestra cada cliente junto.
    return (entry.customer_code, entry.company, entry.tracking_project)
