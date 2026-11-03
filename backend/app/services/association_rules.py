"""Validación pura de asociaciones proyecto-cliente; no accede a Smartsheet."""

from collections import defaultdict

from app.models.associations import AssociationIssue
from app.services.smartsheet import RawRow


def validate_associations(
    rows: list[RawRow], catalog: list[RawRow], columns: tuple[str, str, str, str]
) -> list[AssociationIssue]:
    """Detecta referencias desconocidas, ambiguas o asociadas al cliente incorrecto."""
    customer_col, project_col, catalog_customer_col, catalog_project_col = columns
    projects: dict[str, set[str]] = defaultdict(set)
    for row in catalog:
        project = (row.cells.get(catalog_project_col) or "").strip().casefold()
        customer = (row.cells.get(catalog_customer_col) or "").strip().casefold()
        if project:
            projects[project].add(customer)
    issues = []
    for row in rows:
        project = (row.cells.get(project_col) or "").strip()
        customer = (row.cells.get(customer_col) or "").strip()
        if not project:
            continue
        owners = projects.get(project.casefold())
        reason = None
        if not customer:
            reason = "missing_customer"
        elif owners is None:
            reason = "unknown_project"
        elif len(owners) != 1 or "" in owners:
            reason = "ambiguous_project"
        elif customer.casefold() not in owners:
            reason = "wrong_customer"
        if reason:
            issues.append(
                AssociationIssue(
                    row_id=row.id,
                    row_number=row.row_number,
                    customer=customer,
                    project=project,
                    reason=reason,
                )
            )
    return issues
