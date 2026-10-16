import csv
import io

from tests.conftest import writes
from tests.factories import OWNER_EMAIL, SHEET_ID, page, share_json


async def test_export_csv_for_excel(client, smartsheet) -> None:
    smartsheet.get("/shares").respond(
        json={
            "items": [
                share_json("O", OWNER_EMAIL, "OWNER", name="Dueña"),
                share_json("A", "ana@example.com", "EDITOR", name="=HYPERLINK(1)"),
                share_json("W", "beto@example.com", "VIEWER", "WORKSPACE"),
            ]
        }
    )
    smartsheet.get("/users").respond(json=page([{"id": 1, "email": "ana@example.com"}]))
    response = await client.get("/api/export/access.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["x-failed-sheets"] == "0"
    text = response.content.decode("utf-8")
    assert text.startswith("\ufeff")
    rows = list(csv.reader(io.StringIO(text.lstrip("\ufeff")), delimiter=";"))
    assert rows[0][0] == "Hoja" and len(rows) == 4
    ana = next(row for row in rows if row[6] == "ana@example.com")
    assert ana[5] == "'=HYPERLINK(1)"  # fórmula neutralizada
    assert (ana[7], ana[10], ana[11]) == ("Editor", "Sí", "Sí")
    beto = next(row for row in rows if row[6] == "beto@example.com")
    assert (beto[9], beto[10]) == ("Heredado del workspace", "No")
    assert rows[1][1] == SHEET_ID
    assert writes(smartsheet) == []
