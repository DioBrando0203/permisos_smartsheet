"""Copia de conversaciones a Obs (SPEC-B17 CA-02 a CA-07) con Smartsheet simulado y PostgreSQL.

Datos sintéticos; ninguna solicitud sale a Smartsheet.
"""

import json
import re
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx

psycopg = pytest.importorskip("psycopg")

from app.services.ids import pilot  # noqa: E402
from app.services.ids.dry_run import PILOT_WORKSPACE  # noqa: E402
from app.services.ids.monitor import IdMonitor  # noqa: E402
from app.services.obs.rules import ARCHIVE_MARK  # noqa: E402
from app.services.obs.store import ObsStore  # noqa: E402
from app.services.obs.sync import ObsSync, obs_hook  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402
from tests.conftest import BASE, make_settings  # noqa: E402
from tests.test_ids import database  # noqa: E402

database = database
SHEET = int(pilot.PRESENTABLE)
OBS, OTHER = 11, 12
WRITES = {"ids_writes_enabled": True, "ids_transition_approved": True, "app_obs_sync_enabled": True}


class FakeComments:
    """Hoja con columna Obs y conversaciones; PUT con fallos inyectables."""

    def __init__(self) -> None:
        self.obs: dict[int, str | None] = {1: "10.08 -  Awaiting confirmation.", 2: None}
        self.discussions: list[dict] = []
        self.workspace = PILOT_WORKSPACE
        self.columns = ["Obs", "Other"]
        self.puts: list[tuple[int, str]] = []
        self.posts: list[tuple[int, str]] = []
        self.put_failures: list[str] = []
        self.next_id = 9000

    def comment(self, row: int | None, text: str, when: str) -> None:
        self.next_id += 1
        self.discussions.append(
            {
                "id": self.next_id + 50000,
                "parentType": "ROW" if row else "SHEET",
                "parentId": row or SHEET,
                "comments": [{"id": self.next_id, "text": text, "createdAt": when}],
            }
        )

    def handle(self, request: httpx.Request) -> httpx.Response:
        rest = re.fullmatch(rf"/2\.0/sheets/{SHEET}(/.*)?", request.url.path).group(1) or ""
        if rest == "/columns":
            data = [
                {"id": [OBS, OTHER][i], "title": t, "index": i} for i, t in enumerate(self.columns)
            ]
            return httpx.Response(200, json={"data": data, "pageNumber": 1, "totalPages": 1})
        if rest == "/discussions":
            return httpx.Response(
                200, json={"data": self.discussions, "pageNumber": 1, "totalPages": 1}
            )
        if request.method == "PUT" and rest == "/rows":
            return self._put(json.loads(request.content), request)
        if request.method == "POST" and rest.endswith("/discussions"):
            row = int(rest.split("/")[2])
            text = json.loads(request.content)["comment"]["text"]
            self.posts.append((row, text))
            self.comment(row, text, "2026-11-12T20:00:00Z")
            return httpx.Response(200, json={"result": {"comments": [{"id": self.next_id}]}})
        if rest.startswith("/rows/"):
            row = int(rest.removeprefix("/rows/"))
            if row not in self.obs:
                return httpx.Response(404, json={"errorCode": 1006, "message": "Not Found"})
            cells = [{"columnId": OBS, "value": self.obs[row]}]
            return httpx.Response(200, json={"id": row, "cells": cells})
        rows = [
            {"id": row, "cells": [{"columnId": OBS, "value": v}]} for row, v in self.obs.items()
        ]
        sheet = {"id": SHEET, "workspace": {"id": int(self.workspace)}}
        return httpx.Response(200, json=sheet | {"rows": rows, "totalRowCount": len(rows)})

    def _put(self, body: list, request: httpx.Request) -> httpx.Response:
        failure = self.put_failures.pop(0) if self.put_failures else None
        if failure == "timeout":
            raise httpx.ReadTimeout("sin respuesta simulada", request=request)
        if failure == "rejected":
            return httpx.Response(400, json={"errorCode": 1012, "message": "Rechazado"})
        row, value = int(body[0]["id"]), body[0]["cells"][0]["value"]
        self.obs[row] = value
        self.puts.append((row, value))
        if failure == "error_applied":
            return httpx.Response(500, json={"errorCode": 4000, "message": "Error simulado"})
        return httpx.Response(200, json={"message": "SUCCESS", "resultCode": 0})


@pytest.fixture
def fake():
    state = FakeComments()
    with respx.mock(assert_all_called=False) as router:
        router.route(url__startswith=f"{BASE}/sheets/").mock(side_effect=state.handle)
        yield state


def _sync(client: SmartsheetClient, dsn: str, **overrides) -> ObsSync:
    settings = make_settings(**(WRITES | overrides))
    return ObsSync(settings, client, ObsStore(dsn), zone=ZoneInfo("America/Lima"), interval=0)


def _recorded(dsn: str) -> int:
    with psycopg.connect(dsn) as conn:
        return conn.execute("SELECT count(*) FROM obs_comentario").fetchone()[0]


async def test_copies_new_comments_once_and_keeps_existing_text(fake, database) -> None:
    fake.comment(1, "Sent the app.", "2026-11-12T17:38:00Z")
    fake.comment(1, "#interno solo para el equipo", "2026-11-12T17:39:00Z")
    fake.comment(2, "Permit approved.\nPick up tomorrow.", "2026-11-13T15:00:00Z")
    fake.comment(None, "Comentario de la hoja", "2026-11-12T17:40:00Z")
    client = SmartsheetClient(make_settings())
    sync = _sync(client, database)
    assert await sync.run() == {
        "rows": 2,
        "comments": 2,
        "archived": 0,
        "waiting_rows": 0,
        "errors": 0,
    }
    assert fake.obs[1] == "11.12 - Sent the app.\n10.08 -  Awaiting confirmation."
    assert fake.obs[2] == "11.13 - Permit approved. // Pick up tomorrow."
    assert (await sync.run())["rows"] == 0 and len(fake.puts) == 2
    fake.comment(1, "Called the city.", "2026-11-12T22:00:00Z")
    await sync.run()
    assert fake.obs[1].splitlines()[0] == "11.12 - Sent the app. // Called the city."
    assert _recorded(database) == 3
    await client.aclose()


async def test_overflow_archives_oldest_text_in_a_comment(fake, database) -> None:
    old_lines = [f"10.{day:02d} - " + "x" * 300 for day in range(1, 14)]
    fake.obs[1] = "\n".join(old_lines)
    fake.comment(1, "New note.", "2026-11-12T17:38:00Z")
    client = SmartsheetClient(make_settings())
    counts = await _sync(client, database).run()
    assert counts["archived"] == 1 and counts["rows"] == 1
    assert len(fake.obs[1]) <= 4000 and fake.obs[1].startswith("11.12 - New note.")
    archived = fake.posts[0][1]
    assert archived.startswith(ARCHIVE_MARK) and old_lines[-1] in archived
    assert old_lines[-1] not in fake.obs[1]
    # El comentario de archivo no vuelve a copiarse a Obs.
    assert (await _sync(client, database).run())["rows"] == 0
    await client.aclose()


async def test_server_error_with_value_applied_is_recorded(fake, database) -> None:
    fake.comment(2, "a", "2026-11-12T17:38:00Z")
    fake.put_failures = ["error_applied"]
    client = SmartsheetClient(make_settings())
    assert (await _sync(client, database).run())["rows"] == 1
    assert _recorded(database) == 1
    await client.aclose()


async def test_unapplied_or_rejected_write_is_retried_later(fake, database) -> None:
    fake.comment(2, "a", "2026-11-12T17:38:00Z")
    fake.put_failures = ["timeout", "rejected"]
    client = SmartsheetClient(make_settings())
    sync = _sync(client, database)
    assert (await sync.run())["errors"] == 1
    assert (await sync.run())["errors"] == 1
    assert _recorded(database) == 0 and fake.obs[2] is None
    assert (await sync.run())["rows"] == 1 and fake.obs[2] == "11.12 - a"
    await client.aclose()


async def test_barriers_block_writes(fake, database) -> None:
    fake.comment(2, "a", "2026-11-12T17:38:00Z")
    client = SmartsheetClient(make_settings())
    fake.workspace = "123"
    with pytest.raises(ValueError, match="Pruebas"):
        await _sync(client, database).run()
    fake.workspace = PILOT_WORKSPACE
    fake.columns = ["Notes", "Other"]
    with pytest.raises(ValueError, match="Obs"):
        await _sync(client, database).run()
    assert fake.puts == []
    assert obs_hook(make_settings(**WRITES | {"app_obs_sync_enabled": False}), client) is None
    assert obs_hook(make_settings(**WRITES | {"app_read_only": True}), client) is None
    assert obs_hook(make_settings(**WRITES), client, database) is not None
    await client.aclose()


async def test_interval_skips_calls_between_passes(fake, database) -> None:
    client = SmartsheetClient(make_settings())
    ticks = iter([0.0, 5.0, 40.0])
    sync = ObsSync(
        make_settings(**WRITES),
        client,
        ObsStore(database),
        zone=ZoneInfo("America/Lima"),
        interval=30,
        clock=lambda: next(ticks),
    )
    first = await sync.run()
    fake.comment(2, "a", "2026-11-12T17:38:00Z")
    assert await sync.run() is first and fake.obs[2] is None
    assert (await sync.run())["rows"] == 1
    await client.aclose()


async def test_monitor_keeps_obs_result_and_isolates_failures(monkeypatch) -> None:
    import app.services.ids.monitor as module

    report = {"counts": {}, "pending_or_conflicting_rows": []}
    monkeypatch.setattr(module, "build_dry_run_report", AsyncMock(return_value=report))
    hook = AsyncMock(return_value={"rows": 1})
    monitor = IdMonitor(AsyncMock(), True, 60, connector_factory=AsyncMock, obs_sync=hook)
    await monitor.run_cycle()
    assert monitor.last_obs == {"rows": 1}
    hook.side_effect = RuntimeError("falla")
    result = await monitor.run_cycle()
    assert result["counts"] == {}
    assert monitor.last_obs == {"error": "obs_sync_failed", "type": "RuntimeError"}
    # En simulación no se escribe Obs.
    simulation = IdMonitor(AsyncMock(), True, 60, obs_sync=hook)
    await simulation.run_cycle()
    assert hook.await_count == 2


async def test_comments_of_deleted_rows_are_ignored(fake, database) -> None:
    fake.comment(77, "fila borrada", "2026-11-12T17:00:00Z")
    fake.comment(2, "a", "2026-11-12T17:38:00Z")
    client = SmartsheetClient(make_settings())
    sync = ObsSync(
        make_settings(**WRITES),
        client,
        ObsStore(database),
        zone=ZoneInfo("America/Lima"),
        interval=0,
        max_rows=1,
    )
    counts = await sync.run()
    assert counts["rows"] == 1 and counts["errors"] == 0 and counts["waiting_rows"] == 0
    assert fake.obs[2] == "11.12 - a" and 77 not in fake.obs
    await client.aclose()
