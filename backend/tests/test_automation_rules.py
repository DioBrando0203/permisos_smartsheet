from app.services.automation_rules import RuleFacts, diagnose, recipient_columns, status_of
from app.services.smartsheet import RawAutomation, RawColumn

COLUMNS = {
    "10": RawColumn("10", "Designer1", 1, False, "PICKLIST"),
    "11": RawColumn("11", "Designer (contacto)", 2, False, "CONTACT_LIST"),
}


def rule(**overrides: object) -> RawAutomation:
    values: dict = {
        "id": "r1",
        "name": "Aviso",
        "enabled": True,
        "disabled_reason": None,
        "disabled_reason_text": None,
        "action_type": "NOTIFICATION_ACTION",
        "frequency": "IMMEDIATELY",
        "recipient_emails": [],
        "recipient_column_ids": ["11"],
        "notify_all_shared": False,
        "modified_at": None,
        "modified_by": None,
    }
    values.update(overrides)
    return RawAutomation(**values)


def codes(item: RawAutomation, unshared: list[str] | None = None) -> list[str]:
    facts = RuleFacts(item, recipient_columns(item, COLUMNS), unshared or [])
    return [problem.code for problem in diagnose(facts)]


def test_healthy_rule() -> None:
    item = rule()
    assert codes(item) == []
    assert status_of(item, []) == "ok"


def test_disabled_by_smartsheet_and_manually() -> None:
    assert "DISABLED_NO_RECIPIENTS" in codes(
        rule(enabled=False, disabled_reason="NO_POTENTIAL_RECIPIENTS")
    )
    assert codes(rule(enabled=False)) == ["DISABLED"]
    assert status_of(rule(enabled=False), []) == "disabled"


def test_recipient_problems() -> None:
    assert codes(rule(recipient_column_ids=[])) == ["NO_RECIPIENTS"]
    assert codes(rule(recipient_column_ids=["99"])) == ["RECIPIENT_COLUMN_MISSING"]
    assert codes(rule(recipient_column_ids=["10"])) == ["RECIPIENT_COLUMN_NOT_CONTACT"]
    emailed = rule(recipient_column_ids=[], recipient_emails=["a@example.com"])
    assert codes(emailed, ["a@example.com"]) == ["RECIPIENT_NOT_SHARED"]
    assert codes(rule(recipient_column_ids=[], notify_all_shared=True)) == []
