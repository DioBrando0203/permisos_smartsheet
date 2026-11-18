"""Listas de asignación desde `Contact List` (SPEC-B20 HP-19).

Smartsheet simulado y datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re

import httpx
import respx

from app.services.childsheets.contacts import ContactOptions, Person, team_options
from app.services.childsheets.sync import child_hooks
from app.services.ids import pilot
from app.services.ids.dry_run import PILOT_WORKSPACE
from app.services.smartsheet import SmartsheetClient
from tests.conftest import BASE, make_settings
from tests.test_childsheets import WRITES

DIRECTORY = "444"
ON = WRITES | {"app_contact_options_enabled": True, "app_contacts_sheet_id": DIRECTORY}


def test_team_lists_only_active_people_with_email() -> None:
    people = [
        Person("Zeta", "persona2@example.com", frozenset({"Permits"}), True),
        Person("Alfa", "persona1@example.com", frozenset({"Permits", "Design"}), True),
        Person("Sin correo", "", frozenset({"Permits"}), True),
        Person("Inactiva", "persona3@example.com", frozenset({"Permits"}), False),
        Person("Repetida", "PERSONA1@example.com", frozenset({"Permits"}), True),
    ]
    assert team_options(people, "Permits") == [
        ("Alfa", "persona1@example.com"),
        ("Zeta", "persona2@example.com"),
    ]
    assert team_options(people, "Records") == []


class Directory:
    """Maestra con 4 columnas de asignación y `Contact List`; registra cada cambio de lista."""

    TITLES = ("Designers", "Permitting Team", "Records Owner", "DT Owner")

    def __init__(self, people: list[tuple[str, str, str, bool]]) -> None:
        self.people = people
        old = [{"name": "Persona Vieja", "email": "persona9@example.com"}]
        self.lists = {
            title: {"contactOptions": list(old), "validation": False} for title in self.TITLES
        }
        self.puts: list[dict] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "PUT":
            column = int(re.search(r"/columns/(\d+)", path).group(1))
            body = json.loads(request.content)
            self.puts.append(body)
            self.lists[self.TITLES[column - 1]] = body
            return httpx.Response(200, json={"message": "SUCCESS"})
        if path.endswith("/columns"):
            data = self._master_columns() if f"/{pilot.PRESENTABLE}/" in path else self._columns()
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        workspace = {"id": int(PILOT_WORKSPACE)}
        return httpx.Response(200, json={"id": 1, "workspace": workspace, "rows": self._rows()})

    def _master_columns(self) -> list[dict]:
        kinds = ("MULTI_CONTACT_LIST", "CONTACT_LIST", "CONTACT_LIST", "CONTACT_LIST")
        return [
            {"id": i + 1, "title": t, "index": i, "type": kinds[i]} | self.lists[t]
            for i, t in enumerate(self.TITLES)
        ]

    def _columns(self) -> list[dict]:
        kinds = (("Name", "TEXT_NUMBER"), ("Email", "CONTACT_LIST"))
        kinds += (("Teams", "MULTI_PICKLIST"), ("Active", "CHECKBOX"))
        return [{"id": i + 1, "title": t, "index": i, "type": k} for i, (t, k) in enumerate(kinds)]

    def _rows(self) -> list[dict]:
        rows = []
        for i, (name, email, teams, active) in enumerate(self.people):
            cells = [{"columnId": 1, "value": name}, {"columnId": 4, "value": active}]
            cells.append({"columnId": 3, "displayValue": teams, "value": teams})
            if email:
                contact = {"objectType": "CONTACT", "email": email, "name": name}
                cells.append({"columnId": 2, "value": email, "objectValue": contact})
            rows.append({"id": i + 1, "cells": cells})
        return rows


async def test_assignment_lists_follow_the_directory_and_never_go_empty() -> None:
    fake = Directory(
        [
            ("Persona Dos", "persona2@example.com", "Design, Permits", True),
            ("Persona Uno", "persona1@example.com", "Permits", True),
            ("Persona Tres", "persona3@example.com", "Records", False),
        ]
    )
    settings = make_settings(**ON)
    client = SmartsheetClient(settings)
    try:
        with respx.mock(assert_all_called=False) as mock:
            mock.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=fake.handle)
            first = await ContactOptions(settings, client, interval=0).run()
            second = await ContactOptions(settings, client, interval=0).run()
    finally:
        await client.aclose()
    assert first == {"updated": 2, "empty": 2, "active": 2} and second["updated"] == 0
    permits = fake.lists["Permitting Team"]
    assert [o["email"] for o in permits["contactOptions"]] == [
        "persona2@example.com",
        "persona1@example.com",
    ]
    assert permits["validation"] is True and permits["type"] == "CONTACT_LIST"
    assert fake.lists["Designers"]["type"] == "MULTI_CONTACT_LIST"
    # Sin nadie activo en Records ni en Design Tickets: sus listas quedan como estaban.
    assert fake.lists["Records Owner"]["contactOptions"][0]["email"] == "persona9@example.com"
    assert fake.lists["DT Owner"]["validation"] is False


def test_contact_lists_step_runs_last_and_only_when_enabled() -> None:
    assert "contacts" not in child_hooks(make_settings(**WRITES), None)
    hooks = child_hooks(make_settings(**ON | {"ids_project_options_enabled": True}), None)
    assert list(hooks)[-2:] == ["options", "contacts"]
