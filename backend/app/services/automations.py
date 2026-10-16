"""Salud de las automatizaciones de Smartsheet (SPEC-B10). Sólo lectura.

Cruza cada regla con las columnas de la hoja (¿la columna de destinatarios es de contacto?) y
con sus permisos (¿el destinatario tiene la hoja compartida?).
"""

import asyncio
from collections import Counter

from app.core.errors import AppError
from app.models.automations import (
    AccountAutomations,
    Automation,
    AutomationSheetRow,
    SheetAutomations,
)
from app.models.people import FailedSheet
from app.services import automation_rules
from app.services.activity_rules import to_author
from app.services.cache import TtlCache
from app.services.search import matches
from app.services.shares import ShareService
from app.services.sheets import SheetService
from app.services.smartsheet import RawAutomation, RawColumn, RawSheet, SmartsheetClient


class AutomationService:
    def __init__(
        self,
        client: SmartsheetClient,
        cache: TtlCache,
        sheets: SheetService,
        shares: ShareService,
    ) -> None:
        self._client = client
        self._cache = cache
        self._sheets = sheets
        self._shares = shares

    async def sheet(self, sheet_id: str, *, refresh: bool = False) -> SheetAutomations:
        summary = await self._sheets.get(sheet_id)
        automations = await self._diagnosed(sheet_id, refresh=refresh)
        return SheetAutomations(
            sheet=summary,
            counts=dict(Counter(item.status for item in automations)),
            automations=automations,
        )

    async def account(
        self, query: str | None, only_problems: bool, *, refresh: bool = False
    ) -> AccountAutomations:
        # Las hojas de otras personas no se pueden abrir con este token (PEN-14).
        sheets = [
            sheet
            for sheet in await self._sheets.raw_sheets(refresh=refresh)
            if sheet.in_my_list and matches(query, sheet.name)
        ]
        results = await asyncio.gather(*(self._safe(sheet, refresh) for sheet in sheets))
        rows = [row for row in results if isinstance(row, AutomationSheetRow)]
        failed = [row for row in results if isinstance(row, FailedSheet)]
        with_rules = [row for row in rows if sum(row.counts.values())]
        shown = [row for row in with_rules if row.problems] if only_problems else with_rules
        return AccountAutomations(
            sheets_reviewed=len(rows),
            sheets_with_rules=len(with_rules),
            rules_total=sum(sum(row.counts.values()) for row in rows),
            by_status=dict(sum((Counter(row.counts) for row in rows), Counter())),
            by_problem=dict(sum((Counter(row.problems) for row in rows), Counter())),
            sheets=sorted(shown, key=lambda row: (-sum(row.problems.values()), row.sheet_name)),
            failed_sheets=failed,
        )

    async def _safe(self, sheet: RawSheet, refresh: bool) -> AutomationSheetRow | FailedSheet:
        """Una hoja que falla se informa y no detiene la revisión de la cuenta (Bulkhead)."""
        try:
            automations = await self._diagnosed(sheet.id, refresh=refresh)
        except AppError as error:
            return FailedSheet(sheet_id=sheet.id, sheet_name=sheet.name, code=error.code)
        problems = Counter(problem.code for item in automations for problem in item.problems)
        return AutomationSheetRow(
            sheet_id=sheet.id,
            sheet_name=sheet.name,
            counts=dict(Counter(item.status for item in automations)),
            problems=dict(problems),
        )

    async def _diagnosed(self, sheet_id: str, *, refresh: bool) -> list[Automation]:
        rules = await self._rules(sheet_id, refresh=refresh)
        if not rules:
            return []
        needs_columns = any(rule.recipient_column_ids for rule in rules)
        columns = {c.id: c for c in await self._sheets.columns(sheet_id)} if needs_columns else {}
        shared = {
            share.email
            for share in await self._shares.raw_shares(sheet_id, refresh=refresh)
            if share.email
        }
        return [_automation(rule, columns, shared) for rule in rules]

    async def _rules(self, sheet_id: str, *, refresh: bool) -> list[RawAutomation]:
        async def load() -> list[RawAutomation]:
            return await self._client.list_automation_rules(sheet_id)

        return await self._cache.get_or_load(f"automations:{sheet_id}", load, refresh=refresh)


def _automation(rule: RawAutomation, columns: dict[str, RawColumn], shared: set[str]) -> Automation:
    recipient_columns = automation_rules.recipient_columns(rule, columns)
    unshared = [email for email in rule.recipient_emails if email not in shared]
    facts = automation_rules.RuleFacts(rule, recipient_columns, unshared)
    problems = automation_rules.diagnose(facts)
    return Automation(
        id=rule.id,
        name=rule.name,
        enabled=rule.enabled,
        status=automation_rules.status_of(rule, problems),
        action_type=rule.action_type,
        frequency=rule.frequency,
        recipient_emails=rule.recipient_emails,
        recipient_columns=recipient_columns,
        notify_all_shared=rule.notify_all_shared,
        smartsheet_reason=rule.disabled_reason_text,
        problems=problems,
        modified_at=rule.modified_at,
        modified_by=to_author(rule.modified_by),
    )
