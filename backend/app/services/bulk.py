"""Operaciones masivas con simulación por defecto (SPEC-B06, ADR-B13).

Planifica con `bulk_plans` y, sólo si se pide ejecutar, reutiliza `ShareService` para cada
paso: mismas reglas, modo solo lectura e invalidación de caché que una operación individual.
"""

from collections import Counter
from collections.abc import Awaitable
from itertools import groupby

from app.core.errors import AppError
from app.models.bulk import BulkStep, CopyPlan, CopyRequest, RevokePlan, RevokeRequest
from app.models.people import Person, PersonSheetAccess
from app.models.shares import Recipient, ShareCreate
from app.models.sheets import SheetSummary
from app.services.bulk_plans import PlannedStep, StepAction, plan_copy
from app.services.people import PeopleService
from app.services.permissions import AccessLevel, ShareType
from app.services.shares import ShareService
from app.services.sheets import SheetService

# Smartsheet acepta hasta 50 destinatarios por alta en este panel (SPEC-B02).
_CREATE_BATCH = 50


class BulkService:
    def __init__(self, sheets: SheetService, shares: ShareService, people: PeopleService) -> None:
        self._sheets = sheets
        self._shares = shares
        self._people = people

    async def copy(self, target_id: str, request: CopyRequest) -> CopyPlan:
        source_id = await self._sheets.resolve_id(request.source_sheet_id)
        if source_id == target_id:
            raise AppError("SAME_SHEET", "La hoja origen y la destino son la misma.", 422)
        if not request.dry_run:
            self._shares.ensure_writable()
        source, target = await self._sheets.get(source_id), await self._sheets.get(target_id)
        planned = plan_copy(
            await self._shares.raw_shares(source_id, refresh=True),
            await self._shares.raw_shares(target_id, refresh=True),
            upgrade_levels=request.upgrade_levels,
            include_inherited=request.include_inherited,
        )
        steps = [_copy_step(item, target) for item in planned]
        if not request.dry_run:
            await self._execute_copy(target_id, planned, steps)
        return CopyPlan(
            source=source,
            target=target,
            dry_run=request.dry_run,
            counts=_counts(steps),
            steps=steps,
        )

    async def revoke(self, key: str, request: RevokeRequest) -> RevokePlan:
        if not request.dry_run:
            self._shares.ensure_writable()
        detail = await self._people.detail(key)
        wanted = set(request.sheet_ids) if request.sheet_ids else None
        accesses = [a for a in detail.sheets if wanted is None or a.sheet_id in wanted]
        steps = [_revoke_step(access, detail.person.key, detail.person) for access in accesses]
        if not request.dry_run:
            for step in steps:
                if step.action is StepAction.REMOVE:
                    await self._run(step, self._shares.delete(step.sheet_id, step.share_id or ""))
        return RevokePlan(
            person=detail.person, dry_run=request.dry_run, counts=_counts(steps), steps=steps
        )

    async def _execute_copy(
        self, target_id: str, planned: list[PlannedStep], steps: list[BulkStep]
    ) -> None:
        creates = [
            (p, s) for p, s in zip(planned, steps, strict=True) if p.action is StepAction.CREATE
        ]
        creates.sort(key=lambda pair: str(pair[0].new_level))
        for level, group in groupby(creates, key=lambda pair: pair[0].new_level):
            batch = list(group)
            for start in range(0, len(batch), _CREATE_BATCH):
                await self._create_batch(target_id, level, batch[start : start + _CREATE_BATCH])
        for plan, step in zip(planned, steps, strict=True):
            if plan.action is StepAction.UPGRADE and plan.share_id and plan.new_level:
                await self._run(step, self._shares.update(target_id, plan.share_id, plan.new_level))

    async def _create_batch(
        self, target_id: str, level: AccessLevel, batch: list[tuple[PlannedStep, BulkStep]]
    ) -> None:
        recipients = [
            Recipient(group_id=p.person.group_id)
            if p.person.type is ShareType.GROUP
            else Recipient(email=p.person.email)
            for p, _ in batch
        ]
        request = ShareCreate(recipients=recipients, access_level=level, send_email=False)
        try:
            await self._shares.create(target_id, request)
        except AppError as error:
            for _, step in batch:
                step.status, step.error_code = "failed", error.code
            return
        for _, step in batch:
            step.status = "done"

    async def _run(self, step: BulkStep, call: Awaitable[object]) -> None:
        """Ejecuta un paso aislado: un fallo se anota y el resto continúa (Bulkhead)."""
        try:
            await call
        except AppError as error:
            step.status, step.error_code = "failed", error.code
            return
        step.status = "done"


def _copy_step(item: PlannedStep, target: SheetSummary) -> BulkStep:
    actionable = item.action in {StepAction.CREATE, StepAction.UPGRADE}
    return BulkStep(
        action=item.action,
        status="planned" if actionable else "not_applicable",
        key=item.person.key,
        type=item.person.type,
        name=item.person.name,
        email=item.person.email,
        sheet_id=target.id,
        sheet_name=target.name,
        share_id=item.share_id,
        current_level=item.current_level,
        new_level=item.new_level,
        reason=item.reason,
    )


def _revoke_step(access: PersonSheetAccess, key: str, person: Person) -> BulkStep:
    removable = access.editable
    return BulkStep(
        action=StepAction.REMOVE if removable else StepAction.SKIP,
        status="planned" if removable else "not_applicable",
        key=key,
        type=person.type,
        name=person.name,
        email=person.email,
        sheet_id=access.sheet_id,
        sheet_name=access.sheet_name,
        share_id=access.share_id,
        current_level=access.access_level,
        reason=None if removable else str(access.locked_reason),
    )


def _counts(steps: list[BulkStep]) -> dict[str, int]:
    return dict(Counter(str(step.action) for step in steps))
