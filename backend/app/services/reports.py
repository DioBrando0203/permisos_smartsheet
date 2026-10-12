"""Auditoría, comparación de hojas y resumen de acceso (SPEC-B05). Sólo lectura."""

import asyncio
from collections import Counter
from datetime import UTC, datetime, timedelta

from app.core.errors import AppError
from app.models.people import FailedSheet
from app.models.reports import (
    AccessSummary,
    AlertPerson,
    AuditAlert,
    ComparePerson,
    DomainCount,
    SheetAccessRow,
    SheetAudit,
    SheetComparison,
)
from app.services.audit_rules import Rule, build_facts, domain_of, evaluate, is_personal
from app.services.bulk_plans import PersonLevel, effective_levels
from app.services.directory import SheetShares, person_key
from app.services.people import PeopleService
from app.services.permissions import AccessLevel, ShareType, rank
from app.services.search import matches
from app.services.shares import ShareService
from app.services.sheets import SheetService
from app.services.smartsheet import RawShare, RawSheet


class ReportService:
    def __init__(self, sheets: SheetService, shares: ShareService, people: PeopleService) -> None:
        self._sheets = sheets
        self._shares = shares
        self._people = people

    async def audit(self, sheet_id: str, *, refresh: bool = False) -> SheetAudit:
        sheet = await self._sheets.get(sheet_id)
        shares = await self._shares.raw_shares(sheet_id, refresh=refresh)
        org_emails = await self.org_emails()
        contacts = {contact.email for contact in await self._people.raw_contacts()}
        facts = build_facts(shares, org_emails, contacts)
        users = [item for item in facts if item.share.type is ShareType.USER]
        return SheetAudit(
            sheet=sheet,
            total=len(shares),
            by_level=dict(Counter(str(share.access_level) for share in shares)),
            by_scope=dict(Counter(str(share.scope) for share in shares)),
            by_domain=_domains(shares),
            org_known=org_emails is not None,
            external_count=None
            if org_emails is None
            else sum(1 for item in users if item.is_external),
            unnamed_count=sum(1 for item in users if not item.share.name),
            not_in_contacts_count=sum(1 for item in users if not item.is_contact),
            alerts=[_alert(rule, affected) for rule, affected in evaluate(facts)],
        )

    async def compare(self, sheet_a: str, sheet_b: str) -> SheetComparison:
        if sheet_a == sheet_b:
            raise AppError("SAME_SHEET", "Elija dos hojas distintas para comparar.", 422)
        summary_a, summary_b = await asyncio.gather(
            self._sheets.get(sheet_a), self._sheets.get(sheet_b)
        )
        levels_a = effective_levels(await self._shares.raw_shares(sheet_a))
        levels_b = effective_levels(await self._shares.raw_shares(sheet_b))
        only_a = [_compare(p, p, None) for k, p in levels_a.items() if k not in levels_b]
        only_b = [_compare(p, None, p) for k, p in levels_b.items() if k not in levels_a]
        both = [k for k in levels_a if k in levels_b]
        differences = [
            _compare(levels_a[k], levels_a[k], levels_b[k])
            for k in both
            if levels_a[k].level is not levels_b[k].level
        ]
        return SheetComparison(
            a=summary_a,
            b=summary_b,
            only_in_a=_by_label(only_a),
            only_in_b=_by_label(only_b),
            level_differences=_by_label(differences),
            same_count=len(both) - len(differences),
        )

    async def access_summary(
        self, query: str | None, inactive_days: int | None, *, refresh: bool = False
    ) -> AccessSummary:
        sheets = [
            s for s in await self._sheets.raw_sheets(refresh=refresh) if matches(query, s.name)
        ]
        results = await asyncio.gather(*(self._people.sheet_shares(s, refresh) for s in sheets))
        org_emails = await self.org_emails()
        cutoff = datetime.now(UTC) - timedelta(days=inactive_days) if inactive_days else None
        rows = [
            _summary_row(item, org_emails, cutoff)
            for item in results
            if isinstance(item, SheetShares)
        ]
        rows.sort(key=lambda row: (-row.share_count, row.sheet_name.casefold()))
        failed = [item for item in results if isinstance(item, FailedSheet)]
        return AccessSummary(sheets=rows, failed_sheets=failed)

    async def org_emails(self) -> set[str] | None:
        users = await self._people.raw_org_users()
        return None if users is None else {user.email for user in users}


def _domains(shares: list[RawShare]) -> list[DomainCount]:
    counts = Counter(domain_of(share.email) for share in shares if share.email)
    return [
        DomainCount(domain=domain, count=count, is_personal=is_personal(f"x@{domain}"))
        for domain, count in counts.most_common()
        if domain
    ]


def _alert(rule: Rule, affected: list[RawShare]) -> AuditAlert:
    people = [
        AlertPerson(
            key=person_key(share.type, share.email, share.group_id or share.user_id),
            type=share.type,
            name=share.name,
            email=share.email,
            access_level=share.access_level,
        )
        for share in sorted(affected, key=lambda s: (-rank(s.access_level), s.email or ""))
    ]
    return AuditAlert(
        code=rule.code,
        severity=rule.severity,
        message=rule.message,
        count=len(people),
        people=people,
    )


def _compare(person: PersonLevel, a: PersonLevel | None, b: PersonLevel | None) -> ComparePerson:
    return ComparePerson(
        key=person.key,
        type=person.type,
        name=person.name,
        email=person.email,
        level_a=a.level if a else None,
        level_b=b.level if b else None,
    )


def _by_label(people: list[ComparePerson]) -> list[ComparePerson]:
    return sorted(people, key=lambda p: (p.name or p.email or p.key).casefold())


def _summary_row(
    item: SheetShares, org_emails: set[str] | None, cutoff: datetime | None
) -> SheetAccessRow:
    sheet: RawSheet = item.sheet
    people = [p for p in effective_levels(item.shares).values() if p.level is not AccessLevel.OWNER]
    users = [p for p in people if p.type is ShareType.USER]
    return SheetAccessRow(
        sheet_id=sheet.id,
        sheet_name=sheet.name,
        modified_at=sheet.modified_at,
        share_count=len(people),
        editors_count=sum(1 for p in people if rank(p.level) >= rank(AccessLevel.EDITOR)),
        external_count=None
        if org_emails is None
        else sum(1 for p in users if p.email not in org_emails),
        personal_email_count=sum(1 for p in users if is_personal(p.email)),
        is_inactive=bool(cutoff and sheet.modified_at and sheet.modified_at < cutoff),
    )
