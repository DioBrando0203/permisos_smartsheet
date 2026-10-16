"""Diagnóstico puro de una automatización de Smartsheet (SPEC-B10). Sin E/S.

Tabla de problemas (P-26): cada entrada dice cuándo aplica y qué mensaje ve el usuario.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.models.automations import AutomationProblem, RecipientColumn
from app.services.smartsheet import RawAutomation, RawColumn

# Sólo las columnas de contacto guardan correos a los que Smartsheet puede avisar.
CONTACT_TYPES = frozenset({"CONTACT_LIST", "MULTI_CONTACT_LIST"})
NO_RECIPIENTS_REASON = "NO_POTENTIAL_RECIPIENTS"


@dataclass(frozen=True)
class RuleFacts:
    rule: RawAutomation
    columns: list[RecipientColumn]
    unshared_emails: list[str]


@dataclass(frozen=True)
class Problem:
    code: str
    applies: Callable[[RuleFacts], bool]
    message: Callable[[RuleFacts], str]


def _titles(columns: list[RecipientColumn]) -> str:
    return ", ".join(column.title or column.id for column in columns)


PROBLEMS: tuple[Problem, ...] = (
    Problem(
        "DISABLED_NO_RECIPIENTS",
        lambda f: not f.rule.enabled and f.rule.disabled_reason == NO_RECIPIENTS_REASON,
        lambda f: "Smartsheet la apagó porque no encontró a quién avisar.",
    ),
    Problem(
        "DISABLED",
        lambda f: not f.rule.enabled and f.rule.disabled_reason != NO_RECIPIENTS_REASON,
        lambda f: (
            "Está apagada"
            + (f" ({f.rule.disabled_reason_text})" if f.rule.disabled_reason_text else ".")
            + ("" if f.rule.disabled_reason_text else " Se puede activar desde Automatización.")
        ),
    ),
    Problem(
        "NO_RECIPIENTS",
        lambda f: (
            not f.rule.recipient_emails
            and not f.rule.recipient_column_ids
            and not f.rule.notify_all_shared
        ),
        lambda f: "No tiene destinatarios: ni correos, ni columnas, ni todos los compartidos.",
    ),
    Problem(
        "RECIPIENT_COLUMN_MISSING",
        lambda f: any(not column.exists for column in f.columns),
        lambda f: "Avisa a una columna que ya no existe en la hoja.",
    ),
    Problem(
        "RECIPIENT_COLUMN_NOT_CONTACT",
        lambda f: any(column.exists and not column.is_contact for column in f.columns),
        lambda f: (
            "Avisa a columnas que no son de contacto ("
            + _titles([c for c in f.columns if c.exists and not c.is_contact])
            + "): sólo tienen texto, no correos. Cámbielas a tipo contacto o use otra columna."
        ),
    ),
    Problem(
        "RECIPIENT_NOT_SHARED",
        lambda f: bool(f.unshared_emails),
        lambda f: (
            f"{len(f.unshared_emails)} destinatario(s) no tienen la hoja compartida; "
            "Smartsheet puede no avisarles."
        ),
    ),
)


def recipient_columns(rule: RawAutomation, columns: dict[str, RawColumn]) -> list[RecipientColumn]:
    result: list[RecipientColumn] = []
    for column_id in rule.recipient_column_ids:
        column = columns.get(column_id)
        result.append(
            RecipientColumn(
                id=column_id,
                title=column.title if column else None,
                type=column.type if column else None,
                is_contact=bool(column and column.type in CONTACT_TYPES),
                exists=column is not None,
            )
        )
    return result


def diagnose(facts: RuleFacts) -> list[AutomationProblem]:
    return [
        AutomationProblem(code=problem.code, message=problem.message(facts))
        for problem in PROBLEMS
        if problem.applies(facts)
    ]


def status_of(rule: RawAutomation, problems: list[AutomationProblem]) -> str:
    if not rule.enabled:
        return "disabled"
    return "with_problems" if problems else "ok"
