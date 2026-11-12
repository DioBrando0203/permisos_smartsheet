"""Reglas puras de la columna Obs (SPEC-B17): formato, unión con el texto actual y límite."""

from collections.abc import Iterable
from datetime import datetime, tzinfo

from app.services.smartsheet.types import RawComment

LIMIT = 4000
ARCHIVE_MARK = "[Obs archive]"
SEPARATOR = " // "
TITLE_MARK = "**"
_SKIP_PREFIXES = ("#interno", "#internal", ARCHIVE_MARK.casefold())
_ELLIPSIS = "…"


def is_skipped(text: str) -> bool:
    """Vacíos, internos y archivos del servicio no pasan a Obs (OB-06)."""
    clean = text.strip().casefold()
    return not clean or clean.startswith(_SKIP_PREFIXES)


def clean_text(text: str) -> str:
    """Una sola línea: los saltos de línea de un comentario se unen con ` // ` (OB-03)."""
    return SEPARATOR.join(part.strip() for part in text.splitlines() if part.strip())


def day_label(moment: datetime, zone: tzinfo) -> str:
    local = moment.astimezone(zone)
    return f"{local.month:02d}.{local.day:02d}"


def is_title(text: str) -> bool:
    """Un comentario o una línea que empieza con `**` es título de sección (OB-16)."""
    return text.strip().startswith(TITLE_MARK)


def compose(current: str | None, comments: Iterable[RawComment], zone: tzinfo) -> str:
    """Agrega los comentarios en orden cronológico sin tocar el texto actual (OB-04, OB-16)."""
    lines = current.split("\n") if current else []
    dated = sorted(
        (item for item in comments if item.created_at is not None and not is_skipped(item.text)),
        key=lambda item: (item.created_at, item.id),
    )
    for item in dated:
        text = clean_text(item.text)
        if is_title(text):
            _add_title(lines, text)
        else:
            _add_entry(lines, day_label(item.created_at, zone), text)  # type: ignore[arg-type]
    return "\n".join(lines)


def _add_title(lines: list[str], title: str) -> None:
    """Sección nueva arriba; una línea en blanco la separa de la sección anterior."""
    if lines and lines[0].strip():
        lines.insert(0, "")
    lines.insert(0, title)


def _add_entry(lines: list[str], label: str, text: str) -> None:
    """Debajo de los títulos de arriba; se une con ` // ` a la primera línea del mismo día."""
    at = 0
    while at < len(lines) and is_title(lines[at]):
        at += 1
    if at < len(lines) and lines[at].startswith(f"{label} -"):
        lines[at] = f"{lines[at].rstrip()}{SEPARATOR}{text}"
    else:
        lines.insert(at, f"{label} - {text}")


def fit(value: str, limit: int = LIMIT) -> tuple[str, str]:
    """(lo que cabe en Obs, lo que se archiva). Se archivan las líneas más antiguas (OB-07)."""
    if len(value) <= limit:
        return value, ""
    kept = value.split("\n")
    archived: list[str] = []
    while len(kept) > 1 and len("\n".join(kept)) > limit:
        archived.insert(0, kept.pop())
    text = "\n".join(kept)
    if len(text) > limit:
        # Una sola línea más larga que la celda: se recorta y se archiva completa.
        archived.insert(0, text)
        text = text[: limit - len(_ELLIPSIS)] + _ELLIPSIS
    return text, "\n".join(archived)


def archive_comments(archived: str, stamp: str, limit: int = LIMIT) -> list[str]:
    """Comentarios `[Obs archive]` de hasta `limit` caracteres con el texto que salió de Obs."""
    header = f"{ARCHIVE_MARK} {stamp}\n"
    size = limit - len(header)
    return [header + archived[start : start + size] for start in range(0, len(archived), size)]
