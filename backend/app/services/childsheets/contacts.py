"""Listas de las columnas de asignación de la maestra desde `Contact List` (SPEC-B20 HP-19).

`Contact List` es el directorio: una fila por persona con `Name`, `Email`, `Teams` y `Active`.
Cada columna de asignación ofrece sólo a las personas activas y con correo de su equipo, y
acepta sólo valores de la lista. Un equipo sin nadie activo no toca su columna: nunca se vacía.
"""

from dataclasses import dataclass

from app.core.config import Settings
from app.services.childsheets.cells import LEVEL, Paced, check_barriers, columns, value
from app.services.ids import pilot
from app.services.smartsheet import SmartsheetClient

NAME, EMAIL, TEAMS, ACTIVE = "Name", "Email", "Teams", "Active"
# Columna de asignación de la maestra y su equipo en `Teams`.
TEAM_COLUMNS = (
    ("Designers", "Design"),
    ("Permitting Team", "Permits"),
    ("Records Owner", "Records"),
    ("DT Owner", "Design Tickets"),
)
CONTACT_TYPES = frozenset({"CONTACT_LIST", "MULTI_CONTACT_LIST"})
Contact = tuple[str, str]  # (nombre, correo)


@dataclass(frozen=True)
class Person:
    name: str
    email: str
    teams: frozenset[str]
    active: bool


def team_options(people: list[Person], team: str) -> list[Contact]:
    """Personas activas y con correo del equipo, por nombre; cada correo una sola vez."""
    found: dict[str, Contact] = {}
    for person in people:
        if person.active and person.email and team in person.teams:
            found.setdefault(person.email.casefold(), (person.name or person.email, person.email))
    return sorted(found.values(), key=lambda contact: contact[0].casefold())


def same_options(current: tuple[Contact, ...], wanted: list[Contact]) -> bool:
    def key(contacts) -> list[tuple[str, str]]:
        return [(name.strip(), email.casefold()) for name, email in contacts]

    return key(current) == key(wanted)


class ContactOptions(Paced):
    def __init__(
        self, settings: Settings, client: SmartsheetClient, *, interval: float = 30.0
    ) -> None:
        super().__init__(interval)
        self.settings = settings
        self.client = client

    async def run(self) -> dict:
        if not self.due():
            return self.last or {}
        directory = self.settings.app_contacts_sheet_id
        await check_barriers(self.settings, self.client, pilot.PRESENTABLE, directory)
        people = await read_people(self.client, directory)
        cols = await columns(self.client, pilot.PRESENTABLE, ())
        updated = empty = 0
        for title, team in TEAM_COLUMNS:
            column = cols.get(title)
            if column is None or column.type not in CONTACT_TYPES:
                continue
            wanted = team_options(people, team)
            if not wanted:
                empty += 1
            elif not (column.validation and same_options(column.contacts, wanted)):
                await self.client.set_contact_options(
                    pilot.PRESENTABLE, column.id, column.type, wanted
                )
                updated += 1
        active = sum(1 for person in people if person.active and person.email)
        self.last = {"updated": updated, "empty": empty, "active": active}
        return self.last


async def read_people(client: SmartsheetClient, sheet: str) -> list[Person]:
    """Personas del directorio `Contact List` (también para los avisos de metraje, FH-05c)."""
    cols = await columns(client, sheet, (NAME, EMAIL, TEAMS, ACTIVE))
    wanted = [cols[title].id for title in (NAME, EMAIL, TEAMS, ACTIVE)]
    rows = await client.list_rows(sheet, wanted, objects=True, level=LEVEL)
    people = []
    for row in rows:
        teams = str(value(row, cols[TEAMS]) or "")
        people.append(
            Person(
                name=str(value(row, cols[NAME]) or ""),
                email=row.contacts.get(cols[EMAIL].id, ""),
                teams=frozenset(t.strip() for t in teams.split(",") if t.strip()),
                active=value(row, cols[ACTIVE]) is True,
            )
        )
    return people
