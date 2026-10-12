"""Búsqueda de texto sin tildes ni mayúsculas."""

import unicodedata


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def matches(query: str | None, *fields: str | None) -> bool:
    """`True` si cada palabra de la consulta aparece en alguno de los campos."""
    words = normalize(query or "").split()
    if not words:
        return True
    haystack = " ".join(normalize(field) for field in fields if field)
    return all(word in haystack for word in words)
