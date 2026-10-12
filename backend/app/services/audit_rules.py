"""Reglas puras de auditoría de una hoja (SPEC-B05): qué acceso merece una alerta y por qué.

Tabla de reglas (P-26): agregar una regla es agregar una entrada, no un `if` en el servicio.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.services.permissions import AccessLevel, ShareType, rank
from app.services.smartsheet import RawShare

# Dominios de correo personales: un plan de un cliente editado desde cuentas personales
# escapa al control de la empresa (no se puede desactivar la cuenta al irse la persona).
PERSONAL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "hotmail.es",
        "outlook.com",
        "outlook.es",
        "live.com",
        "msn.com",
        "yahoo.com",
        "yahoo.es",
        "icloud.com",
        "me.com",
        "aol.com",
        "proton.me",
        "protonmail.com",
    }
)
SHARING_LEVELS = frozenset({AccessLevel.ADMIN, AccessLevel.EDITOR_SHARE})
SEVERITY_RANK = {"info": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class ShareFacts:
    """Un permiso con lo que se sabe de la persona fuera de la hoja."""

    share: RawShare
    is_external: bool | None  # None: no se pudo leer la organización
    is_contact: bool


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str
    message: str
    applies: Callable[[ShareFacts], bool]


def build_facts(
    shares: list[RawShare], org_emails: set[str] | None, contacts: set[str]
) -> list[ShareFacts]:
    """Une cada permiso con lo conocido de la persona; `org_emails=None` si no se pudo leer."""
    return [
        ShareFacts(
            share=share,
            is_external=None if org_emails is None else share.email not in org_emails,
            is_contact=share.email in contacts,
        )
        for share in shares
    ]


def domain_of(email: str | None) -> str | None:
    return email.rsplit("@", 1)[1] if email and "@" in email else None


def is_personal(email: str | None) -> bool:
    return domain_of(email) in PERSONAL_DOMAINS


def _is_user(facts: ShareFacts) -> bool:
    return facts.share.type is ShareType.USER


RULES: tuple[Rule, ...] = (
    Rule(
        "EXTERNAL_CAN_SHARE",
        "high",
        "Personas fuera de la organización que pueden compartir la hoja con cualquiera.",
        lambda f: _is_user(f) and f.is_external is True and f.share.access_level in SHARING_LEVELS,
    ),
    Rule(
        "PERSONAL_EMAIL_CAN_EDIT",
        "medium",
        "Correos personales con permiso de edición o superior.",
        lambda f: (
            is_personal(f.share.email) and rank(f.share.access_level) >= rank(AccessLevel.EDITOR)
        ),
    ),
    Rule(
        "UNNAMED",
        "info",
        "Personas sin nombre en Smartsheet: sólo se conoce su correo.",
        lambda f: _is_user(f) and not f.share.name,
    ),
    Rule(
        "NOT_IN_CONTACTS",
        "info",
        "Personas con acceso que no están en la libreta de contactos.",
        lambda f: _is_user(f) and not f.is_contact,
    ),
)


def evaluate(facts: list[ShareFacts]) -> list[tuple[Rule, list[RawShare]]]:
    """Reglas con al menos una persona afectada, en el orden de la tabla.

    El propietario nunca genera alertas: es la cuenta que administra la hoja.
    """
    candidates = [item for item in facts if item.share.access_level is not AccessLevel.OWNER]
    hits: list[tuple[Rule, list[RawShare]]] = []
    for rule in RULES:
        affected = _unique([item.share for item in candidates if rule.applies(item)])
        if affected:
            hits.append((rule, affected))
    return hits


def _unique(shares: list[RawShare]) -> list[RawShare]:
    """Una persona puede tener permiso propio y heredado: se informa una vez."""
    seen: dict[str, RawShare] = {}
    for share in shares:
        key = share.email or f"group-{share.group_id}"
        if key not in seen or rank(share.access_level) > rank(seen[key].access_level):
            seen[key] = share
    return list(seen.values())
