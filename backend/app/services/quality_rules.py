"""Revisiones puras de calidad de datos (SPEC-B09): repetidos, vacíos y formato. Sin E/S."""

import re
from collections import defaultdict

from app.models.quality import QualityIssue, QualityRow
from app.services.smartsheet import RawRow

# Límites contra expresiones costosas y valores enormes: la expresión la escribe quien consulta.
MAX_PATTERN_LENGTH = 100
MAX_VALUE_LENGTH = 500
MAX_ISSUES = 200


def duplicates(rows: list[RawRow], column_id: str) -> list[QualityIssue]:
    """Valores repetidos, sin distinguir mayúsculas ni espacios a los lados; vacíos no cuentan."""
    groups: dict[str, list[RawRow]] = defaultdict(list)
    shown: dict[str, str] = {}
    for row in rows:
        value = (row.cells.get(column_id) or "").strip()
        if not value:
            continue
        key = value.casefold()
        groups[key].append(row)
        shown.setdefault(key, value)
    issues = [
        QualityIssue(value=shown[key], rows=[_row(row) for row in group])
        for key, group in groups.items()
        if len(group) > 1
    ]
    return sorted(issues, key=lambda issue: (-len(issue.rows), issue.value or ""))


def missing(rows: list[RawRow], column_id: str) -> list[QualityIssue]:
    empty = [_row(row) for row in rows if not (row.cells.get(column_id) or "").strip()]
    return [QualityIssue(value=None, rows=empty)] if empty else []


def mismatches(rows: list[RawRow], column_id: str, pattern: re.Pattern[str]) -> list[QualityIssue]:
    """Valores no vacíos que no cumplen la expresión, agrupados por valor."""
    groups: dict[str, list[RawRow]] = defaultdict(list)
    for row in rows:
        value = (row.cells.get(column_id) or "").strip()
        if value and not pattern.search(value[:MAX_VALUE_LENGTH]):
            groups[value].append(row)
    issues = [QualityIssue(value=v, rows=[_row(r) for r in group]) for v, group in groups.items()]
    return sorted(issues, key=lambda issue: (-len(issue.rows), issue.value or ""))


def normalized_values(rows: list[RawRow], column_id: str) -> set[str]:
    """Valores no vacíos de una columna, sin espacios a los lados ni mayúsculas."""
    return {value.casefold() for row in rows if (value := (row.cells.get(column_id) or "").strip())}


def missing_references(rows: list[RawRow], column_id: str, catalog: set[str]) -> list[QualityIssue]:
    """Valores no vacíos que no están en el catálogo, agrupados por valor."""
    groups: dict[str, list[RawRow]] = defaultdict(list)
    shown: dict[str, str] = {}
    for row in rows:
        value = (row.cells.get(column_id) or "").strip()
        if value and value.casefold() not in catalog:
            groups[value.casefold()].append(row)
            shown.setdefault(value.casefold(), value)
    issues = [QualityIssue(value=shown[k], rows=[_row(r) for r in g]) for k, g in groups.items()]
    return sorted(issues, key=lambda issue: (-len(issue.rows), issue.value or ""))


def compile_pattern(expression: str) -> re.Pattern[str] | None:
    """Expresión válida y acotada, o `None` si no se puede usar."""
    if not expression or len(expression) > MAX_PATTERN_LENGTH:
        return None
    try:
        return re.compile(expression)
    except re.error:
        return None


def issue_count(issues: list[QualityIssue]) -> int:
    """Filas afectadas: una fila repetida o vacía cuenta una vez por revisión."""
    return sum(len(issue.rows) for issue in issues)


def _row(row: RawRow) -> QualityRow:
    return QualityRow(row_id=row.id, row_number=row.row_number, label=row.label)
