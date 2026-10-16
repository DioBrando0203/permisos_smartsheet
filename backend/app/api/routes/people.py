from typing import Literal

from fastapi import APIRouter

from app.api.deps import ServicesDep
from app.models.people import Contact, Group, PeopleResponse, PersonDetail

router = APIRouter()

PeopleFilter = Literal["contacts", "org", "external", "groups", "with_access", "without_access"]


@router.get("/users")
async def list_people(
    services: ServicesDep,
    q: str | None = None,
    only: PeopleFilter | None = None,
    refresh: bool = False,
) -> PeopleResponse:
    """Directorio: contactos, usuarios de la organización y quien tiene acceso a alguna hoja.

    La primera carga lee los permisos de todas las hojas y puede tardar.
    """
    return await services.people.list(q, only, refresh=refresh)


@router.get("/users/{key}")
async def person_detail(services: ServicesDep, key: str) -> PersonDetail:
    """Una persona (por correo) o grupo (`group-<id>`) y sus hojas con nivel."""
    return await services.people.detail(key)


@router.get("/contacts")
async def list_contacts(services: ServicesDep, refresh: bool = False) -> list[Contact]:
    """Libreta de contactos del dueño del token en Smartsheet (sólo lectura)."""
    return await services.people.contacts(refresh=refresh)


@router.get("/groups")
async def list_groups(services: ServicesDep, refresh: bool = False) -> list[Group]:
    return await services.people.groups(refresh=refresh)
