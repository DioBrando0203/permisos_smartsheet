"""Reglas puras del catálogo de proyectos y de Linked Tracking (SPEC-B16), datos sintéticos."""

from app.services.catalog_rules import (
    LinkStatus,
    Origin,
    ProjectRow,
    build_catalog,
    classify_link,
    filter_catalog,
)

CUSTOMERS = ("BS-Blue Stream", "CC-Crown Castle", "OT-Others")


def project(row_id: str, stable: str, code: str, linked: str = "", company: str = "KMV"):
    customer = next(option for option in CUSTOMERS if option.startswith(f"{code}-")) if code else ""
    return ProjectRow(row_id, None, stable, stable, customer, code, company, linked)


ROWS = [
    project("1", "KMV-BS-27-001", "BS"),
    project("2", "KMV-BS-27-002", "BS"),
    project("3", "KMV-CC-27-001", "CC"),
    project("4", "KMV-OT-27-001", "OT"),
    project("5", "GALP-BS-27-001", "BS", company="GALP"),
    ProjectRow("6", None, "", "KMV-BS-27-003", "BS-Blue Stream", "BS", "KMV", ""),
]


def catalog() -> dict:
    entries, _ = build_catalog(ROWS, ["KMV-CC-26-563", "texto libre", "KMV-BS-27-001"], CUSTOMERS)
    return {entry.tracking_project: entry for entry in entries}


def test_catalog_has_permanent_and_historical_projects_grouped_by_customer() -> None:
    entries, duplicates = build_catalog(
        ROWS + [project("7", "KMV-BS-27-001", "BS")], ["KMV-CC-26-563", "texto libre"], CUSTOMERS
    )
    values = [entry.tracking_project for entry in entries]
    # Sin Stable ID todavía no entra; un texto sin formato de proyecto tampoco.
    assert "KMV-BS-27-003" not in values and "texto libre" not in values
    assert duplicates == ["KMV-BS-27-001"]
    assert values.count("KMV-BS-27-001") == 1
    historical = next(entry for entry in entries if entry.tracking_project == "KMV-CC-26-563")
    assert historical.origin == Origin.HISTORICAL
    assert historical.customer == "CC-Crown Castle"
    assert [entry.customer_code for entry in entries] == sorted(e.customer_code for e in entries)


def test_filters_bs_cc_ot_and_company() -> None:
    entries = list(catalog().values())
    assert {e.tracking_project for e in filter_catalog(entries, "bs", None)} == {
        "KMV-BS-27-001",
        "KMV-BS-27-002",
        "GALP-BS-27-001",
    }
    assert {e.tracking_project for e in filter_catalog(entries, "CC", None)} == {
        "KMV-CC-27-001",
        "KMV-CC-26-563",
    }
    assert [e.tracking_project for e in filter_catalog(entries, "OT", None)] == ["KMV-OT-27-001"]
    assert [e.tracking_project for e in filter_catalog(entries, "BS", "GALP")] == ["GALP-BS-27-001"]
    assert filter_catalog(entries, "ZY", None) == []


def test_linked_tracking_classification() -> None:
    data = catalog()
    cases = {
        "": LinkStatus.EMPTY,
        "KMV-BS-27-002": LinkStatus.CURRENT_VALID,
        "KMV-BS-27-001": LinkStatus.SAME_PROJECT,
        "KMV-CC-27-001": LinkStatus.OTHER_CUSTOMER,
        "KMV-CC-26-999": LinkStatus.OTHER_CUSTOMER,
        "KMV-BS-25-120": LinkStatus.UNVERIFIABLE,
        "proyecto viejo": LinkStatus.INVALID,
        "GALP-BS-27-001": LinkStatus.CURRENT_VALID,
    }
    for linked, expected in cases.items():
        row = project("1", "KMV-BS-27-001", "BS", linked)
        assert classify_link(row, data) == expected, linked
    historical = project("3", "KMV-CC-27-001", "CC", "KMV-CC-26-563")
    assert classify_link(historical, data) == LinkStatus.HISTORICAL_VALID
    # Cliente cambiado después de asociar: la referencia anterior deja de corresponder.
    changed = project("3", "KMV-CC-27-001", "BS", "KMV-CC-26-563")
    assert classify_link(changed, data) == LinkStatus.OTHER_CUSTOMER
    no_customer = project("8", "KMV-BS-27-009", "", "KMV-BS-27-002")
    assert classify_link(no_customer, data) == LinkStatus.UNVERIFIABLE
