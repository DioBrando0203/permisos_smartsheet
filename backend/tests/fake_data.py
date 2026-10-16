"""Datos sintéticos del Smartsheet falso (ADR-10 del frontend). Nada es real.

Reproduce los casos que importan a la interfaz: hoja de otra persona, propio y heredado con el
mismo id (B-05), permiso sin nombre, correo personal con nivel Administrador, fila de
encabezados copiada, Record ID repetido, diseñador fuera del catálogo y reglas rotas.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

PLAN_2026 = "1111111111111111"
PLAN_2025 = "2222222222222222"
CATALOG = "3333333333333333"
FOREIGN = "4444444444444444"
GROUP_ID = "5555555555555555"
OWNER = "duena@example.com"
PLAN_COLUMNS = [
    "Primary",
    "Record ID",
    "Designer1",
    "Designer2",
    "Project Status",
    "Construction Manager",
]
_COLUMN_TYPES = ["TEXT_NUMBER", "TEXT_NUMBER", "PICKLIST", "PICKLIST", "PICKLIST", "CONTACT_LIST"]

Json = dict[str, Any]


def iso(days_ago: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed() -> Json:
    """Estado inicial completo; `reset` vuelve a esto."""
    return {
        "me": {
            "id": 9000000000000001,
            "email": OWNER,
            "firstName": "Dueña",
            "lastName": "Prueba",
            "admin": True,
            "account": {"id": 1, "name": "Cuenta de prueba"},
        },
        "sheets": [
            _sheet(PLAN_2026, "Plan 2026", "FakePlan2026", 0),
            _sheet(PLAN_2025, "Plan 2025", "FakePlan2025", 20),
            _sheet(CATALOG, "Source Designers", "FakeCatalog", 90),
        ],
        "org_sheets": [{"id": int(FOREIGN), "name": "Plan ajeno", "owner": "otra@example.com"}],
        "users": [
            _user(9000000000000001, OWNER, "Dueña", "Prueba", 0, admin=True),
            _user(9000000000000002, "ana@example.com", "Ana", "Pérez", 1),
            _user(9000000000000003, "luis@example.com", "Luis", "Gómez", 150),
        ],
        "contacts": [
            {"id": "c1", "email": "ana@example.com", "name": "Ana Pérez"},
            {"id": "c2", "email": "luis@example.com", "name": "Luis Gómez"},
            {"id": "c3", "email": "beto@hotmail.com", "name": "Beto"},
            {"id": "c4", "email": "sola@example.com", "name": "Sola Sin Hojas"},
        ],
        "groups": [
            {"id": int(GROUP_ID), "name": "Equipo diseño", "description": None, "memberCount": 3}
        ],
        "shares": _shares(),
        "columns": {
            PLAN_2026: _plan_columns(),
            PLAN_2025: _plan_columns(),
            CATALOG: _catalog_columns(),
        },
        "rows": {PLAN_2026: _rows_2026(), PLAN_2025: _rows_2025(), CATALOG: _catalog_rows()},
        "automations": _automations(),
        "next_share": 1,
    }


def _sheet(sheet_id: str, name: str, code: str, days: int) -> Json:
    return {
        "id": int(sheet_id),
        "name": name,
        "accessLevel": "OWNER",
        "permalink": f"https://app.smartsheet.com/sheets/{code}",
        "modifiedAt": iso(days),
    }


def _user(
    user_id: int, email: str, first: str, last: str, days: int, *, admin: bool = False
) -> Json:
    return {
        "id": user_id,
        "email": email,
        "firstName": first,
        "lastName": last,
        "admin": admin,
        "status": "ACTIVE",
        "lastLogin": iso(days),
    }


def share(
    share_id: str,
    email: str | None,
    level: str,
    *,
    scope: str = "ITEM",
    name: str | None = None,
    group: bool = False,
) -> Json:
    data: Json = {
        "id": share_id,
        "type": "GROUP" if group else "USER",
        "accessLevel": level,
        "scope": scope,
    }
    if group:
        data |= {"groupId": GROUP_ID, "name": name}
        return data
    data |= {"email": email, "userId": str(abs(hash(email)) % 10**15)}
    if name:
        data["name"] = name
    return data


def _shares() -> dict[str, list[Json]]:
    owner = [
        share("S-OWN", OWNER, "OWNER", name="Dueña Prueba"),
        share("S-OWN", OWNER, "OWNER", scope="WORKSPACE", name="Dueña Prueba"),
    ]
    return {
        PLAN_2026: owner
        + [
            share("S-ANA", "ana@example.com", "EDITOR", name="Ana Pérez"),
            share("S-LUIS", "luis@example.com", "VIEWER"),
            share("S-BETO", "beto@hotmail.com", "ADMIN", name="Beto"),
            share("S-GRP", None, "EDITOR", name="Equipo diseño", group=True),
        ],
        PLAN_2025: owner[:1]
        + [
            share("S-ANA25", "ana@example.com", "EDITOR_SHARE", name="Ana Pérez"),
            share("S-LUIS25", "luis@example.com", "EDITOR"),
            share("S-NUEVO", "nuevo@example.com", "VIEWER"),
        ],
        CATALOG: owner[:1],
        FOREIGN: [share("S-OTRA", "otra@example.com", "OWNER", name="Otra Persona")],
    }


def _plan_columns() -> list[Json]:
    return [
        {"id": 100 + n, "title": title, "index": n, "primary": n == 0, "type": _COLUMN_TYPES[n]}
        for n, title in enumerate(PLAN_COLUMNS)
    ]


def _catalog_columns() -> list[Json]:
    return [{"id": 200, "title": "Designer", "index": 0, "primary": True, "type": "TEXT_NUMBER"}]


def _row(
    row_id: int, values: list[str | None], editor: str, days: float, column_base: int = 100
) -> Json:
    author = {"email": editor, "name": editor.split("@")[0].title()}
    return {
        "id": row_id,
        "rowNumber": row_id % 100,
        "createdAt": iso(400),
        "createdBy": {"email": OWNER, "name": "Dueña Prueba"},
        "modifiedAt": iso(days),
        "modifiedBy": author,
        "cells": [
            {"columnId": column_base + n, "value": value, "displayValue": value}
            for n, value in enumerate(values)
        ],
    }


def _rows_2026() -> list[Json]:
    return [
        _row(
            7001,
            ["KMV-1", "10521", "Ana Pérez", None, "2. Design Process", None],
            "ana@example.com",
            1,
        ),
        _row(
            7002,
            ["KMV-2", "10521", "Luis Gómez", "Ana Pérez", "4. Permit Process", None],
            "luis@example.com",
            2,
        ),
        _row(7003, ["KMV-3", "By email", None, None, "1. Survey Progress", None], OWNER, 40),
        _row(7004, ["KMV-4", "10530", "Carla Ruiz", None, "COMPLETE", None], "ana@example.com", 3),
        _row(7005, PLAN_COLUMNS[:5] + [None], OWNER, 60),
        _row(
            7006,
            ["KMV-6", "10531", "Ana Pérez", None, "2. Design on Hold", None],
            "ana@example.com",
            5,
        ),
    ]


def _rows_2025() -> list[Json]:
    return [
        _row(
            7101, ["KMV-25-1", "9001", "Ana Pérez", None, "COMPLETE", None], "ana@example.com", 30
        ),
        _row(
            7102,
            ["KMV-25-2", "9002", "Luis Gómez", None, "4. Permit Approved", None],
            "luis@example.com",
            25,
        ),
        _row(7103, ["KMV-25-3", "9003", "Carla Ruiz", None, "IN PROGRESS", None], OWNER, 21),
    ]


def _catalog_rows() -> list[Json]:
    return [_row(7201, ["Ana Pérez"], OWNER, 90, 200), _row(7202, ["Luis Gómez"], OWNER, 90, 200)]


def _rule(
    rule_id: int, name: str, enabled: bool, columns: list[int], reason: str | None = None
) -> Json:
    return {
        "id": rule_id,
        "name": name,
        "enabled": enabled,
        "disabledReason": reason,
        "disabledReasonText": "No recipients." if reason else None,
        "modifiedAt": iso(100),
        "modifiedBy": {"email": OWNER, "name": "Dueña Prueba"},
        "action": {
            "type": "NOTIFICATION_ACTION",
            "frequency": "IMMEDIATELY",
            "recipients": [],
            "recipientColumnIds": columns,
            "notifyAllSharedUsers": False,
        },
    }


def _automations() -> dict[str, list[Json]]:
    return {
        PLAN_2026: [
            _rule(1, "Avisar al Construction Manager", True, [105]),
            _rule(2, "alert", False, [], "NO_POTENTIAL_RECIPIENTS"),
        ],
        PLAN_2025: [_rule(3, "Avisar al diseñador", True, [102])],
        CATALOG: [],
    }
