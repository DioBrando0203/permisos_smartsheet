"""JSON sintético con la forma de Smartsheet (QB-03): correos @example.com e ids inventados."""

from typing import Any

SHEET_ID = "1111111111111111"
OWNER_EMAIL = "duena@example.com"


def sheet_json(sheet_id: str = SHEET_ID, name: str = "Plan 2026", level: str = "OWNER") -> dict:
    return {
        "id": int(sheet_id),
        "name": name,
        "accessLevel": level,
        "permalink": f"https://app.smartsheet.com/sheets/Pk{sheet_id}Code",
        "modifiedAt": "2026-10-01T12:00:00Z",
    }


def share_json(
    share_id: str,
    email: str | None,
    level: str = "EDITOR",
    scope: str = "ITEM",
    *,
    name: str | None = None,
    group_id: str | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": share_id,
        "type": "GROUP" if group_id else "USER",
        "accessLevel": level,
        "scope": scope,
    }
    if group_id:
        data["groupId"] = group_id
    else:
        data["userId"] = str(abs(hash(email)) % 10**15)
        data["email"] = email
    if name:
        data["name"] = name
    return data


def default_shares() -> list[dict[str, Any]]:
    return [
        share_json("S-OWNER", OWNER_EMAIL, "OWNER", name="Dueña"),
        share_json("S-ANA", "ana@example.com", "EDITOR", name="Ana Pérez"),
        share_json("S-LUIS", "luis@example.com", "VIEWER"),
        share_json("S-WS", "beto@example.com", "ADMIN", "WORKSPACE", name="Beto"),
    ]


def me_json() -> dict[str, Any]:
    return {
        "id": 9999999999999,
        "email": OWNER_EMAIL,
        "firstName": "Dueña",
        "lastName": "Prueba",
        "admin": True,
        "account": {"name": "Cuenta de prueba", "id": 1},
    }


def page(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {"pageNumber": 1, "totalPages": 1, "totalCount": len(data), "data": data}
