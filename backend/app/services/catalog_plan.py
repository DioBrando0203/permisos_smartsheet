"""Prepara una comparación de catálogos; no lee ni escribe servicios externos."""

from dataclasses import dataclass
from enum import StrEnum


class CatalogAction(StrEnum):
    ADD = "add"
    UPDATE = "update"
    UNCHANGED = "unchanged"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class Project:
    project_id: str
    customer: str


@dataclass(frozen=True)
class CatalogChange:
    project_id: str
    action: CatalogAction
    customer: str | None


def plan_catalog(source: list[Project], destination: list[Project]) -> list[CatalogChange]:
    """Compara por identificador, sin proponer borrados de referencias históricas."""
    origin = _group(source)
    target = _group(destination)
    result = []
    for key, projects in origin.items():
        title = projects[0].project_id.strip()
        copies = target.get(key, [])
        if len(projects) != 1 or len(copies) > 1 or not projects[0].customer.strip():
            result.append(CatalogChange(title, CatalogAction.CONFLICT, None))
        elif not copies:
            result.append(CatalogChange(title, CatalogAction.ADD, projects[0].customer.strip()))
        elif copies[0].customer.strip().casefold() != projects[0].customer.strip().casefold():
            result.append(CatalogChange(title, CatalogAction.UPDATE, projects[0].customer.strip()))
        else:
            result.append(
                CatalogChange(title, CatalogAction.UNCHANGED, projects[0].customer.strip())
            )
    return sorted(result, key=lambda item: item.project_id.casefold())


def _group(projects: list[Project]) -> dict[str, list[Project]]:
    grouped: dict[str, list[Project]] = {}
    for project in projects:
        key = project.project_id.strip().casefold()
        if not key:
            raise ValueError("Proyecto sin identificador")
        grouped.setdefault(key, []).append(project)
    return grouped
