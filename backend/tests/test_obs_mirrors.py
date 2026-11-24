"""El chat de `Permits` llega al Obs de su fila de la maestra (SPEC-B17 OB-17, CA-09 a CA-11).

Smartsheet simulado y datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import re
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx

psycopg = pytest.importorskip("psycopg")

from app.services.ids.dry_run import PILOT_WORKSPACE  # noqa: E402
from app.services.obs.sources import mirror_sheets  # noqa: E402
from app.services.obs.store import ObsStore  # noqa: E402
from app.services.obs.sync import ObsSync, obs_hook  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import BASE, make_settings  # noqa: E402
from tests.test_ids import database  # noqa: E402
from tests.test_obs_sync import SHEET, WRITES, FakeComments  # noqa: E402

database = database
PERMITS, KEY_COLUMN = "555", 31


class FakePermits:
    """Hoja `Permits`: cada fila con su `Master Row` y sus conversaciones."""

    def __init__(self, master: FakeComments) -> None:
        self.master = master
        self.rows: dict[int, str | None] = {501: "1", 502: "77", 503: None}
        self.discussions: list[dict] = []
        self.workspace = PILOT_WORKSPACE
        self.columns = ["Master Row", "Permit Status"]
        self.next_id = 7000

    def comment(self, row: int, text: str, when: str) -> None:
        self.next_id += 1
        comments = [{"id": self.next_id, "text": text, "createdAt": when}]
        self.discussions.append(
            {"id": self.next_id + 50000, "parentType": "ROW", "parentId": row, "comments": comments}
        )

    def handle(self, request: httpx.Request) -> httpx.Response:
        found = re.fullmatch(rf"/2\.0/sheets/{PERMITS}(/.*)?", request.url.path)
        if found is None:
            return self.master.handle(request)
        rest = found.group(1) or ""
        if rest == "/columns":
            data = [
                {"id": KEY_COLUMN + i, "title": t, "index": i, "type": "TEXT_NUMBER"}
                for i, t in enumerate(self.columns)
            ]
            return self._page(data)
        if rest == "/discussions":
            return self._page(self.discussions)
        rows = [
            {"id": row, "cells": [{"columnId": KEY_COLUMN, "value": key}] if key else []}
            for row, key in self.rows.items()
        ]
        sheet = {"id": int(PERMITS), "workspace": {"id": int(self.workspace)}}
        return httpx.Response(200, json=sheet | {"rows": rows, "totalRowCount": len(rows)})

    def _page(self, data: list) -> httpx.Response:
        return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})


@pytest.fixture
def fake():
    state = FakePermits(FakeComments())
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=state.handle)
        yield state


def _sync(client: SmartsheetClient, dsn: str) -> ObsSync:
    return ObsSync(
        make_settings(**WRITES),
        client,
        ObsStore(dsn),
        zone=ZoneInfo("America/Lima"),
        interval=0,
        mirrors=(PERMITS,),
    )


def _recorded(dsn: str) -> list[tuple[int, int]]:
    with psycopg.connect(dsn) as conn:
        query = "SELECT hoja_id, fila_id FROM obs_comentario ORDER BY comentario_id"
        return [tuple(row) for row in conn.execute(query).fetchall()]


async def test_permit_chat_reaches_the_obs_of_its_master_row(fake, database) -> None:
    fake.master.comment(1, "Sent the app.", "2026-11-12T17:38:00Z")
    fake.comment(501, "City asked for a traffic plan.", "2026-11-12T19:00:00Z")
    fake.comment(501, "#internal call the PM first", "2026-11-12T19:05:00Z")
    fake.comment(502, "Fila de la maestra borrada", "2026-11-12T19:10:00Z")
    fake.comment(503, "Sin Master Row", "2026-11-12T19:20:00Z")
    client = SmartsheetClient(make_settings())
    sync = _sync(client, database)
    assert await sync.run() == {
        "rows": 1,
        "comments": 2,
        "archived": 0,
        "waiting_rows": 0,
        "errors": 0,
    }
    # Un solo Obs, en orden: lo de la maestra y lo del permiso del mismo día en una línea.
    first = "11.12 - Sent the app. // City asked for a traffic plan."
    assert fake.master.obs[1] == f"{first}\n10.08 -  Awaiting confirmation."
    # Cada comentario queda registrado en la hoja y la fila donde está.
    assert _recorded(database) == [(int(PERMITS), 501), (SHEET, 1)]
    assert (await sync.run())["rows"] == 0 and len(fake.master.puts) == 1
    fake.comment(501, "Permit approved.", "2026-11-13T15:00:00Z")
    await sync.run()
    assert fake.master.obs[1].splitlines()[0] == "11.13 - Permit approved."
    await client.aclose()


async def test_a_broken_team_sheet_does_not_stop_the_master(fake, database) -> None:
    fake.master.comment(2, "a", "2026-11-12T17:38:00Z")
    fake.comment(501, "b", "2026-11-12T17:40:00Z")
    fake.columns = ["Permit Status"]
    client = SmartsheetClient(make_settings())
    counts = await _sync(client, database).run()
    assert counts["errors"] == 1 and counts["rows"] == 1
    assert fake.master.obs[2] == "11.12 - a" and fake.master.obs[1].startswith("10.08")
    # Fuera de Pruebas no se lee la hoja de equipo; su comentario queda para después.
    fake.columns = ["Master Row", "Permit Status"]
    fake.workspace = "123"
    assert (await _sync(client, database).run())["errors"] == 1
    fake.workspace = PILOT_WORKSPACE
    assert (await _sync(client, database).run())["comments"] == 1
    assert fake.master.obs[1].startswith("11.12 - b")
    await client.aclose()


async def test_only_permits_reflects_into_obs_and_only_when_enabled() -> None:
    teams = {
        "app_permits_sync_enabled": True,
        "app_permits_sheet_id": PERMITS,
        "app_mot_sync_enabled": True,
        "app_mot_sheet_id": "666",
        "app_billing_sync_enabled": True,
        "app_billing_sheet_id": "888",
    }
    on = WRITES | teams | {"app_obs_mirrors_enabled": True}
    assert mirror_sheets(make_settings(**on)) == (PERMITS,)
    assert mirror_sheets(make_settings(**on | {"app_obs_mirrors_enabled": False})) == ()
    assert mirror_sheets(make_settings(**on | {"app_permits_sync_enabled": False})) == ()
    client = SmartsheetClient(make_settings())
    assert obs_hook(make_settings(**on), client, "dsn") is not None
    await client.aclose()
