from app.services.audit_rules import ShareFacts, evaluate, is_personal
from app.services.bulk_plans import StepAction, plan_copy
from app.services.permissions import AccessLevel, ShareScope, ShareType
from app.services.smartsheet import RawShare


def share(
    email: str, level: str = "EDITOR", scope: str = "ITEM", name: str | None = "Nombre"
) -> RawShare:
    return RawShare(
        id=f"id-{email}",
        type=ShareType.USER,
        user_id=email,
        group_id=None,
        email=email,
        name=name,
        access_level=AccessLevel(level),
        scope=ShareScope(scope),
    )


def facts(item: RawShare, external: bool = False, contact: bool = True) -> ShareFacts:
    return ShareFacts(share=item, is_external=external, is_contact=contact)


def codes(items: list[ShareFacts]) -> list[str]:
    return [rule.code for rule, _ in evaluate(items)]


def test_personal_email_rule() -> None:
    assert is_personal("a@hotmail.com") and not is_personal("a@empresa.com")
    assert codes([facts(share("a@hotmail.com", "EDITOR"))]) == ["PERSONAL_EMAIL_CAN_EDIT"]
    assert codes([facts(share("a@hotmail.com", "VIEWER"))]) == []


def test_external_admin_rule_needs_known_organization() -> None:
    admin = share("x@socio.com", "ADMIN")
    assert codes([facts(admin, external=True)]) == ["EXTERNAL_CAN_SHARE"]
    assert codes([facts(admin, external=False)]) == []
    assert codes([ShareFacts(share=admin, is_external=None, is_contact=True)]) == []


def test_owner_is_never_flagged() -> None:
    owner = share("dueno@hotmail.com", "OWNER", name=None)
    assert codes([facts(owner, external=True, contact=False)]) == []


def test_person_with_item_and_inherited_is_reported_once() -> None:
    items = [
        facts(share("a@x.com", "VIEWER", name=None)),
        facts(share("a@x.com", "EDITOR", "WORKSPACE", None)),
    ]
    ((_, affected),) = evaluate(items)
    assert [s.access_level for s in affected] == [AccessLevel.EDITOR]


def test_owner_is_copied_as_admin() -> None:
    (step,) = plan_copy(
        [share("a@x.com", "OWNER")], [], upgrade_levels=False, include_inherited=False
    )
    assert (step.action, step.new_level) == (StepAction.CREATE, AccessLevel.ADMIN)


def test_copy_never_downgrades() -> None:
    source = [share("a@x.com", "EDITOR"), share("b@x.com", "ADMIN"), share("c@x.com", "VIEWER")]
    target = [share("a@x.com", "VIEWER"), share("b@x.com", "VIEWER"), share("c@x.com", "ADMIN")]
    keep = {
        s.person.email: s.action
        for s in plan_copy(source, target, upgrade_levels=False, include_inherited=False)
    }
    assert keep == {
        "a@x.com": StepAction.KEEP,
        "b@x.com": StepAction.KEEP,
        "c@x.com": StepAction.KEEP,
    }
    up = {
        s.person.email: s.action
        for s in plan_copy(source, target, upgrade_levels=True, include_inherited=False)
    }
    assert up == {
        "a@x.com": StepAction.UPGRADE,
        "b@x.com": StepAction.UPGRADE,
        "c@x.com": StepAction.KEEP,
    }


def test_copy_skips_inherited_and_owner_in_target() -> None:
    source = [share("a@x.com", "ADMIN"), share("o@x.com", "EDITOR")]
    target = [share("a@x.com", "VIEWER", "WORKSPACE"), share("o@x.com", "OWNER")]
    steps = plan_copy(source, target, upgrade_levels=True, include_inherited=False)
    assert {s.person.email: s.reason for s in steps} == {"a@x.com": "INHERITED", "o@x.com": "OWNER"}


def test_source_inherited_only_when_asked() -> None:
    source = [share("w@x.com", "EDITOR", "WORKSPACE")]
    assert plan_copy(source, [], upgrade_levels=False, include_inherited=False) == []
    assert len(plan_copy(source, [], upgrade_levels=False, include_inherited=True)) == 1
