"""Smartsheet falso: imita la API 2.0 que usa el cliente con datos sintéticos (ADR-10, frontend).

Sirve para pruebas de integración y E2E sin tocar la cuenta real: el backend se apunta con
`SMARTSHEET_BASE_URL=http://127.0.0.1:<puerto>/2.0`. Guarda las escrituras recibidas en memoria
para verificarlas (`GET /_fake/writes`) y se reinicia con `POST /_fake/reset`.

Uso manual: `python -m tests.fake_smartsheet --port 8791` desde `backend/`.
"""

import argparse
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from tests import fake_data

Json = dict[str, Any]


class FakeState:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.data = fake_data.seed()
        self.writes: list[Json] = []


def create_fake_app() -> FastAPI:
    state = FakeState()
    app = FastAPI(title="Smartsheet falso")
    app.state.fake = state
    api = APIRouter(prefix="/2.0")

    @app.middleware("http")
    async def require_token(request: Request, call_next):
        # Igual que Smartsheet: sin token, 401 con su código de error.
        if request.url.path.startswith("/2.0") and not request.headers.get("authorization"):
            return _error(401, 1002, "Your Access Token is invalid.")
        return await call_next(request)

    @api.get("/users/me")
    async def me() -> Json:
        return state.data["me"]

    @api.get("/sheets")
    async def sheets(request: Request) -> Json:
        return _page(state.data["sheets"], request)

    @api.get("/users/sheets")
    async def org_sheets(request: Request) -> Json:
        mine = [
            {"id": s["id"], "name": s["name"], "owner": fake_data.OWNER}
            for s in state.data["sheets"]
        ]
        return _page(mine + state.data["org_sheets"], request)

    @api.get("/users")
    async def users(request: Request) -> Json:
        return _page(state.data["users"], request)

    @api.get("/contacts")
    async def contacts(request: Request) -> Json:
        return _page(state.data["contacts"], request)

    @api.get("/groups")
    async def groups(request: Request) -> Json:
        return _page(state.data["groups"], request)

    @api.get("/sheets/{sheet_id}")
    async def sheet(sheet_id: str, request: Request) -> Any:
        info = _find_sheet(state, sheet_id)
        if info is None:
            return _error(404, 1006, "Not Found")
        rows = state.data["rows"].get(sheet_id, [])
        wanted = request.query_params.get("columnIds")
        if not wanted:
            return info | {"totalRowCount": len(rows), "columns": state.data["columns"][sheet_id]}
        ids = {int(x) for x in wanted.split(",")}
        writer = request.query_params.get("include") == "writerInfo"
        shown = [_filter_row(row, ids, writer) for row in rows]
        page, size = _page_params(request, 500)
        return info | {"totalRowCount": len(rows), "rows": shown[(page - 1) * size : page * size]}

    @api.get("/sheets/{sheet_id}/columns")
    async def columns(sheet_id: str, request: Request) -> Any:
        if sheet_id not in state.data["columns"]:
            return _error(404, 1006, "Not Found")
        return _page(state.data["columns"][sheet_id], request)

    @api.get("/sheets/{sheet_id}/rows/{row_id}")
    async def row(sheet_id: str, row_id: int) -> Any:
        found = _find_row(state, sheet_id, row_id)
        return found if found else _error(404, 1006, "Not Found")

    @api.get("/sheets/{sheet_id}/rows/{row_id}/columns/{column_id}/history")
    async def history(sheet_id: str, row_id: int, column_id: int, request: Request) -> Any:
        found = _find_row(state, sheet_id, row_id)
        if not found:
            return _error(404, 1006, "Not Found")
        cell = next((c for c in found["cells"] if c["columnId"] == column_id), {"value": None})
        changes = [
            {
                "columnId": column_id,
                "value": cell["value"],
                "displayValue": cell["value"],
                "modifiedAt": found["modifiedAt"],
                "modifiedBy": found["modifiedBy"],
            },
            {
                "columnId": column_id,
                "value": "Borrador",
                "displayValue": "Borrador",
                "modifiedAt": found["createdAt"],
                "modifiedBy": found["createdBy"],
            },
        ]
        return _page(changes, request)

    @api.get("/sheets/{sheet_id}/automationrules")
    async def automations(sheet_id: str, request: Request) -> Any:
        if sheet_id not in state.data["automations"]:
            return _error(404, 1006, "Not Found")
        return _page(state.data["automations"][sheet_id], request)

    @api.get("/shares")
    async def list_shares(request: Request) -> Json:
        include = request.query_params.get("sharingInclude", "ITEM")
        items = state.data["shares"].get(request.query_params.get("assetId", ""), [])
        return {"items": [s for s in items if s["scope"] in include.split(",")]}

    @api.get("/shares/{share_id}")
    async def get_share(share_id: str, request: Request) -> Any:
        found = _find_share(state, request, share_id)
        return found if found else _error(404, 1006, "Not Found")

    @api.post("/shares")
    async def create_shares(request: Request) -> Json:
        sheet_id = request.query_params["assetId"]
        body = await request.json()
        created = []
        for item in body:
            state.data["next_share"] += 1
            new = fake_data.share(
                f"S-NEW{state.data['next_share']}", item.get("email"), item["accessLevel"]
            )
            state.data["shares"].setdefault(sheet_id, []).append(new)
            created.append(new)
        _record(state, request, body)
        return {"items": created}

    @api.patch("/shares/{share_id}")
    async def update_share(share_id: str, request: Request) -> Any:
        found = _find_share(state, request, share_id)
        if not found:
            return _error(404, 1006, "Not Found")
        body = await request.json()
        found["accessLevel"] = body["accessLevel"]
        _record(state, request, body)
        return found

    @api.delete("/shares/{share_id}")
    async def delete_share(share_id: str, request: Request) -> Any:
        sheet_id = request.query_params.get("assetId", "")
        items = state.data["shares"].get(sheet_id, [])
        kept = [s for s in items if not (s["id"] == share_id and s["scope"] == "ITEM")]
        if len(kept) == len(items):
            return _error(404, 1006, "Not Found")
        state.data["shares"][sheet_id] = kept
        _record(state, request, None)
        return {}

    @app.get("/_fake/writes")
    async def writes() -> list[Json]:
        return state.writes

    @app.post("/_fake/reset")
    async def reset() -> Json:
        state.reset()
        return {"status": "reset"}

    app.include_router(api)
    return app


def _page_params(request: Request, default: int = 100) -> tuple[int, int]:
    return int(request.query_params.get("page", 1)), int(
        request.query_params.get("pageSize", default)
    )


def _page(items: list[Json], request: Request) -> Json:
    page, size = _page_params(request)
    total_pages = max(1, -(-len(items) // size))
    page = min(page, total_pages)  # como /sheets: una página mayor repite la última
    return {
        "pageNumber": page,
        "pageSize": size,
        "totalPages": total_pages,
        "totalCount": len(items),
        "data": items[(page - 1) * size : page * size],
    }


def _find_sheet(state: FakeState, sheet_id: str) -> Json | None:
    # Las hojas de otra persona no se abren con este token (404), como en la cuenta real.
    return next((s for s in state.data["sheets"] if str(s["id"]) == sheet_id), None)


def _find_row(state: FakeState, sheet_id: str, row_id: int) -> Json | None:
    return next((r for r in state.data["rows"].get(sheet_id, []) if r["id"] == row_id), None)


def _find_share(state: FakeState, request: Request, share_id: str) -> Json | None:
    items = state.data["shares"].get(request.query_params.get("assetId", ""), [])
    matches = [s for s in items if s["id"] == share_id]
    return next((s for s in matches if s["scope"] == "ITEM"), matches[0] if matches else None)


def _filter_row(row: Json, column_ids: set[int], writer: bool) -> Json:
    shown = {k: v for k, v in row.items() if k != "cells" and (writer or not k.endswith("By"))}
    shown["cells"] = [cell for cell in row["cells"] if cell["columnId"] in column_ids]
    return shown


def _record(state: FakeState, request: Request, body: Any) -> None:
    state.writes.append(
        {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "body": body,
        }
    )


def _error(status: int, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"errorCode": code, "message": message, "refId": "fake"}, status_code=status
    )


app = create_fake_app()


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="Smartsheet falso con datos sintéticos")
    parser.add_argument("--port", type=int, default=8791)
    uvicorn.run(app, host="127.0.0.1", port=parser.parse_args().port)
