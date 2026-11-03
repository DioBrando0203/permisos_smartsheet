import pytest

from app.services.catalog_plan import CatalogAction, Project, plan_catalog


def test_catalog_plan_keeps_historical_and_reports_conflicts() -> None:
    source = [
        Project("P-01", "BS"),
        Project("P-02", "CC"),
        Project("P-03", "BS"),
        Project("P-04", "BS"),
        Project("p-04", "CC"),
    ]
    destination = [Project("p-01", "bs"), Project("P-02", "BS"), Project("H-01", "CC")]
    plan = plan_catalog(source, destination)
    assert [(item.project_id, item.action) for item in plan] == [
        ("P-01", CatalogAction.UNCHANGED),
        ("P-02", CatalogAction.UPDATE),
        ("P-03", CatalogAction.ADD),
        ("P-04", CatalogAction.CONFLICT),
    ]
    with pytest.raises(ValueError):
        plan_catalog([Project(" ", "BS")], [])
