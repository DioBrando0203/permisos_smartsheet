"""Hojas de métricas de un año de la 2.0 para sus dashboards (KMV_2.0.md K2-106).

Crea en la carpeta del año, dentro de Pruebas, cinco hojas con fórmulas de columna que leen la
maestra del año y sus hojas de equipo por referencias entre hojas: `Customers` (una fila por
cliente y una de todos), `Months` (cliente por mes), `Counties` (cliente por condado),
`Categories` (cliente por `Task`) y `People` (diseño y permisos). Sin celdas fijas: agregar un
cliente o una persona es agregar una fila. Año siguiente: maestra nueva y `--previous-master`.

Uso, desde `backend/`:
`.venv/bin/python ../servicios/dashboards/metricas_anuales.py --year 2026 --folder <id>`
Origen: `backend/.env` u opciones (`--master`...). No toca hojas existentes ni crea fuera de Pruebas.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.core.errors import AppError  # noqa: E402
from app.services.childsheets.contacts import read_people  # noqa: E402
from app.services.smartsheet import SmartsheetClient  # noqa: E402

PRUEBAS = "7965022790936452"
ALL = "All customers"
C = f'OR(@cell = Customer@row, Customer@row = "{ALL}")'
PROJECT = 'OR(@cell = "KMV-P", @cell = "KMV-Miscellaneous")'
PERMIT = 'OR(@cell = "KMV-Permit", @cell = "KMV-Line")'
CANCELLED = 'OR(@cell = "CANCELLED", @cell = "4. Permit Cancelled")'
COUNTIES = ("Dade", "Broward", "Palm Beach", "St Lucie", "St. Lucie", "Martin", "Orange")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
# (prefijo, hoja, columnas) de cada referencia entre hojas.
REFS = {
    "M": (
        "master",
        (
            "Type of Project",
            "Customer",
            "Closed",
            "Project Status",
            "Total Footage",
            "Design Completed Days",
            "PM Approval Days",
            "County",
            "Date Received",
            "Task",
            "Designers",
        ),
    ),
    "P": (
        "permits",
        ("Customer", "Permit - Days in Submitted", "1st Revision Req", "Permitting Team"),
    ),
    "R": ("records", ("Customer", "Records Status", "Tracking Project")),
    "B": ("billing", ("Customer", "Row Type", "Invoice Status")),
}


def avg(range_ref: str, *criteria: str) -> str:
    return f'=IFERROR(ROUND(AVG(COLLECT({range_ref}, {", ".join(criteria)})), 1), "")'


def customers_formulas() -> dict[str, str]:
    base = f"{{M Type of Project}}, {PROJECT}, {{M Customer}}, {C}"
    permits = f"{{M Type of Project}}, {PERMIT}, {{M Customer}}, {C}"
    billing = f'{{B Row Type}}, "Project", {{B Customer}}, {C}, {{B Invoice Status}}'
    return {
        "Projects": f"=COUNTIFS({base})",
        "Active Projects": f"=COUNTIFS({base}, {{M Closed}}, false)",
        "Completed Projects": f"=COUNTIFS({base}, {{M Closed}}, true, {{M Project Status}}, NOT({CANCELLED}))",
        "Cancelled Projects": f"=COUNTIFS({base}, {{M Project Status}}, {CANCELLED})",
        "Permits": f"=COUNTIFS({permits})",
        "Active Permits": f"=COUNTIFS({permits}, {{M Closed}}, false)",
        "Completed Permits": f"=COUNTIFS({permits}, {{M Closed}}, true, {{M Project Status}}, NOT({CANCELLED}))",
        "Cancelled Permits": f"=COUNTIFS({permits}, {{M Project Status}}, {CANCELLED})",
        "Permits by Others": f'=COUNTIFS({permits}, {{M Project Status}}, "4. Permit Process by others")',
        "MOT": f'=COUNTIFS({{M Type of Project}}, "KMV-MOT", {{M Customer}}, {C})',
        "Fiber Footage": f"=SUMIFS({{M Total Footage}}, {base})",
        "Avg Design Days": avg("{M Design Completed Days}", base),
        "Avg PM Approval Days": avg("{M PM Approval Days}", base),
        "Avg Permit Days Submitted": avg("{P Permit - Days in Submitted}", f"{{P Customer}}, {C}"),
        "Permits with 1st Revision": f"=COUNTIFS({{P 1st Revision Req}}, ISDATE(@cell), {{P Customer}}, {C})",
        "Records Requests": f"=COUNTIFS({{R Tracking Project}}, NOT(ISBLANK(@cell)), {{R Customer}}, {C})",
        "Records Received": f'=COUNTIFS({{R Records Status}}, "Received", {{R Customer}}, {C})',
        "Not Invoiced": f'=COUNTIFS({billing}, "NOT INVOICED")',
        "Invoice in Progress": f'=COUNTIFS({billing}, OR(@cell = "GALP INVOICED", @cell = "PM APPROVED"))',
        "Invoice Sent": f'=COUNTIFS({billing}, "SENT TO CUSTOMER")',
        "Invoice Paid": f'=COUNTIFS({billing}, "PAID")',
    }


def months_formulas(year: int, previous: bool) -> dict[str, str]:
    when = f"AND(IFERROR(YEAR(@cell), 0) = {year}, IFERROR(MONTH(@cell), 0) = [Month #]@row)"
    base = f"{{M Customer}}, {C}, {{M Date Received}}, {when}"
    found = {
        "Projects": f"=COUNTIFS({{M Type of Project}}, {PROJECT}, {base})",
        "Permits": f"=COUNTIFS({{M Type of Project}}, {PERMIT}, {base})",
        "MOT": f'=COUNTIFS({{M Type of Project}}, "KMV-MOT", {base})',
        "Fiber Footage": f"=SUMIFS({{M Total Footage}}, {{M Type of Project}}, {PROJECT}, {base})",
    }
    if previous:
        before = when.replace(str(year), str(year - 1))
        found[f"Projects {year - 1}"] = (
            f"=COUNTIFS({{Q Type of Project}}, {PROJECT}, {{Q Customer}}, {C}, {{Q Date Received}}, {before})"
        )
    return found


def counties_formulas(named: list[str]) -> dict[str, str]:
    others = "NOT(OR(" + ", ".join(f'@cell = "{name}"' for name in named) + "))"

    def pick(kind: str) -> str:
        head = f"{{M Type of Project}}, {kind}, {{M Customer}}, {C}, {{M County}}"
        return (
            f'=IF(County@row = "Others", COUNTIFS({head}, {others}), COUNTIFS({head}, County@row))'
        )

    return {"Projects": pick(PROJECT), "Permits": pick(PERMIT), "MOT": pick('"KMV-MOT"')}


def categories_formulas() -> dict[str, str]:
    base = f"{{M Type of Project}}, {PROJECT}, {{M Customer}}, {C}, {{M Task}}, Category@row"
    return {
        "Projects": f"=COUNTIFS({base})",
        "Cancelled Projects": f"=COUNTIFS({base}, {{M Project Status}}, {CANCELLED})",
        "Fiber Footage": f"=SUMIFS({{M Total Footage}}, {base})",
        "Avg Design Days": avg("{M Design Completed Days}", base),
        "Avg PM Approval Days": avg("{M PM Approval Days}", base),
    }


def people_formulas() -> dict[str, str]:
    # Las referencias entre hojas traen el nombre del contacto: se reconoce por nombre o correo.
    designer = f"{{M Designers}}, OR(HAS(@cell, Email@row), HAS(@cell, Name@row)), {{M Type of Project}}, {PROJECT}"
    team = "{P Permitting Team}, OR(@cell = Email@row, @cell = Name@row)"
    return {
        "Projects Designed": f"=COUNTIFS({designer})",
        "Fiber Footage Designed": f"=SUMIFS({{M Total Footage}}, {designer})",
        "Avg Design Days": avg("{M Design Completed Days}", designer),
        "Permits Assigned": f"=COUNTIFS({team})",
        "Avg Permit Days Submitted": avg("{P Permit - Days in Submitted}", team),
    }


class Builder:
    def __init__(self, client: SmartsheetClient, folder: str, sources: dict[str, str]) -> None:
        self.c, self.folder, self.sources = client, folder, sources
        self.source_cols: dict[str, dict[str, str]] = {}

    async def source_columns(self, sheet: str) -> dict[str, str]:
        if sheet not in self.source_cols:
            cols = await self.c.list_columns(sheet)
            self.source_cols[sheet] = {col.title: col.id for col in cols}
        return self.source_cols[sheet]

    async def build(
        self, name: str, labels: list[str], rows: list[list], formulas: dict[str, str]
    ) -> None:
        columns = [{"title": labels[0], "type": "TEXT_NUMBER", "primary": True}]
        columns += [{"title": t, "type": "TEXT_NUMBER"} for t in [*labels[1:], *formulas]]
        made = await self.c._transport.request(
            "POST",
            f"/folders/{self.folder}/sheets",
            json={"name": name, "columns": columns},
            retry=False,
        )
        sheet = str(made["result"]["id"])
        ids = {col["title"]: col["id"] for col in made["result"]["columns"]}
        body = [
            {
                "toBottom": True,
                "cells": [
                    {"columnId": ids[t], "value": v} for t, v in zip(labels, row, strict=True)
                ],
            }
            for row in rows
        ]
        for start in range(0, len(body), 400):
            await self.c._transport.request(
                "POST", f"/sheets/{sheet}/rows", json=body[start : start + 400], retry=False
            )
        used = {
            prefix for text in formulas.values() for prefix in REFS if "{" + prefix + " " in text
        }
        used |= {"Q"} if any("{Q " in text for text in formulas.values()) else set()
        for prefix in sorted(used):
            source_key, titles = REFS["M" if prefix == "Q" else prefix]
            source = self.sources["previous" if prefix == "Q" else source_key]
            cols = await self.source_columns(source)
            for title in titles:
                if any("{" + f"{prefix} {title}" + "}" in text for text in formulas.values()):
                    ref = {
                        "name": f"{prefix} {title}",
                        "sourceSheetId": int(source),
                        "startColumnId": int(cols[title]),
                        "endColumnId": int(cols[title]),
                    }
                    await self.c._transport.request(
                        "POST", f"/sheets/{sheet}/crosssheetreferences", json=ref, retry=False
                    )
        failed = []
        for title, formula in formulas.items():
            try:
                await self.c._transport.request(
                    "PUT",
                    f"/sheets/{sheet}/columns/{ids[title]}",
                    json={"formula": formula, "type": "TEXT_NUMBER"},
                    retry=False,
                )
            except AppError as error:  # se informa y se sigue con las demás columnas
                failed.append(f"{title}: {str(error)[:120]}")
        print(
            f"creada: {name} ({len(rows)} filas, {len(formulas)} métricas)"
            + (f"; sin fórmula: {failed}" if failed else "")
        )


async def main(args: argparse.Namespace) -> int:
    settings = get_settings()
    sources = {
        "master": args.master or settings.ids_master_sheet_id,
        "permits": args.permits or settings.app_permits_sheet_id,
        "records": args.records or settings.app_records_sheet_id,
        "billing": args.billing or settings.app_billing_sheet_id,
        "previous": args.previous_master or "",
    }
    client = SmartsheetClient(settings)
    try:
        for key, sheet in sources.items():
            if sheet and await client.sheet_workspace_id(sheet) != PRUEBAS:
                print(f"La hoja {key} no está en Pruebas: no se crea nada.")
                return 2
        tree = await client._transport.request("GET", f"/folders/{args.folder}")
        existing = {s["name"] for s in tree.get("sheets", [])}
        master_cols = {
            col.title: col for col in await client.list_columns(sources["master"], level=2)
        }
        customers = [o for o in master_cols["Customer"].options]
        tasks = list(master_cols["Task"].options)
        categories = [
            t
            for t in tasks[
                tasks.index("___Project Type___") + 1 : tasks.index("___Permits Type___")
            ]
        ]
        named = [c for c in COUNTIES if c in master_cols["County"].options]
        people = [
            p
            for p in await read_people(client, settings.app_contacts_sheet_id)
            if p.active and p.email and p.teams & {"Design", "Permits"}
        ]
        everyone = [ALL, *customers]
        builder = Builder(client, args.folder, sources)
        plan = [
            ("Customers", ["Customer"], [[c] for c in everyone], customers_formulas()),
            (
                "Months",
                ["Customer", "Month", "Month #"],
                [[c, m, i + 1] for c in everyone for i, m in enumerate(MONTHS)],
                months_formulas(args.year, bool(sources["previous"])),
            ),
            (
                "Counties",
                ["Customer", "County"],
                [[c, k] for c in everyone for k in [*named, "Others"]],
                counties_formulas(named),
            ),
            (
                "Categories",
                ["Customer", "Category"],
                [[c, k] for c in everyone for k in categories],
                categories_formulas(),
            ),
            (
                "People",
                ["Name", "Email", "Teams"],
                [[p.name, p.email, ", ".join(sorted(p.teams))] for p in people],
                people_formulas(),
            ),
        ]
        for suffix, labels, rows, formulas in plan:
            name = f"KMV 2.0 Metrics {args.year} - {suffix}"
            if name in existing:
                print(f"ya existe, no se toca: {name}")
                continue
            await builder.build(name, labels, rows, formulas)
    finally:
        await client.aclose()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hojas de métricas de un año de la 2.0 (K2-106).")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--folder", required=True, help="carpeta del año en Pruebas")
    for option in ("master", "permits", "records", "billing", "previous-master"):
        parser.add_argument(f"--{option}", default="")
    sys.exit(asyncio.run(main(parser.parse_args())))
