"""Revisión de riesgos de toda la cuenta (SPEC-B07). Sólo lectura.

Aplica las mismas reglas de la auditoría por hoja (`audit_rules`) a todas las hojas y agrega
por hoja y por persona. Es la base de las alertas automáticas (PEN-18).
"""

import asyncio
from collections import Counter
from dataclasses import dataclass, field

from app.models.people import FailedSheet
from app.models.reports import AccountReview, ReviewPerson, ReviewSheet, ReviewTotals
from app.services.audit_rules import SEVERITY_RANK, Rule, build_facts, evaluate
from app.services.directory import SheetShares, person_key
from app.services.people import PeopleService
from app.services.permissions import ShareType
from app.services.reports import ReportService
from app.services.search import matches
from app.services.sheets import SheetService
from app.services.smartsheet import RawShare


@dataclass
class _PersonHits:
    """Acumulador de una persona: en qué hojas y con qué alertas aparece."""

    share: RawShare
    codes: set[str] = field(default_factory=set)
    sheets: set[str] = field(default_factory=set)


class AccountReviewService:
    def __init__(self, sheets: SheetService, people: PeopleService, reports: ReportService) -> None:
        self._sheets = sheets
        self._people = people
        self._reports = reports

    async def review(
        self, query: str | None, min_severity: str, *, refresh: bool = False
    ) -> AccountReview:
        sheets = [
            s for s in await self._sheets.raw_sheets(refresh=refresh) if matches(query, s.name)
        ]
        results = await asyncio.gather(*(self._people.sheet_shares(s, refresh) for s in sheets))
        org_emails = await self._reports.org_emails()
        contacts = {contact.email for contact in await self._people.raw_contacts()}
        threshold = SEVERITY_RANK[min_severity]
        rows: list[ReviewSheet] = []
        people: dict[str, _PersonHits] = {}
        for item in results:
            if not isinstance(item, SheetShares):
                continue
            hits = [
                (rule, affected)
                for rule, affected in evaluate(build_facts(item.shares, org_emails, contacts))
                if SEVERITY_RANK[rule.severity] >= threshold
            ]
            if hits:
                rows.append(self._sheet_row(item, hits))
                _collect_people(people, item.sheet.id, hits)
        return AccountReview(
            min_severity=min_severity,
            totals=_totals(len(sheets) - _failed_count(results), rows, people),
            sheets=sorted(rows, key=_sheet_order),
            people=sorted((_person(hit) for hit in people.values()), key=_person_order),
            failed_sheets=[item for item in results if isinstance(item, FailedSheet)],
        )

    def _sheet_row(self, item: SheetShares, hits: list[tuple[Rule, list[RawShare]]]) -> ReviewSheet:
        summary = self._sheets.summary(item.sheet)
        return ReviewSheet(
            sheet_id=summary.id,
            sheet_name=summary.name,
            has_dynamic_view=summary.has_dynamic_view,
            max_severity=max((rule.severity for rule, _ in hits), key=SEVERITY_RANK.__getitem__),
            alerts={rule.code: len(affected) for rule, affected in hits},
        )


def _collect_people(
    people: dict[str, _PersonHits], sheet_id: str, hits: list[tuple[Rule, list[RawShare]]]
) -> None:
    for rule, affected in hits:
        for share in affected:
            item_id = share.group_id if share.type is ShareType.GROUP else share.user_id
            entry = people.setdefault(
                person_key(share.type, share.email, item_id), _PersonHits(share)
            )
            entry.codes.add(rule.code)
            entry.sheets.add(sheet_id)


def _person(hit: _PersonHits) -> ReviewPerson:
    share = hit.share
    item_id = share.group_id if share.type is ShareType.GROUP else share.user_id
    return ReviewPerson(
        key=person_key(share.type, share.email, item_id),
        type=share.type,
        name=share.name,
        email=share.email,
        codes=sorted(hit.codes),
        sheet_count=len(hit.sheets),
    )


def _totals(reviewed: int, rows: list[ReviewSheet], people: dict[str, _PersonHits]) -> ReviewTotals:
    by_code = Counter(code for hit in people.values() for code in hit.codes)
    return ReviewTotals(
        sheets_reviewed=reviewed, sheets_with_alerts=len(rows), people_by_code=dict(by_code)
    )


def _failed_count(results: list[SheetShares | FailedSheet]) -> int:
    return sum(1 for item in results if isinstance(item, FailedSheet))


def _sheet_order(row: ReviewSheet) -> tuple[int, int, str]:
    return (-SEVERITY_RANK[row.max_severity], -sum(row.alerts.values()), row.sheet_name.casefold())


def _person_order(person: ReviewPerson) -> tuple[int, str]:
    return (-person.sheet_count, (person.name or person.email or person.key).casefold())
