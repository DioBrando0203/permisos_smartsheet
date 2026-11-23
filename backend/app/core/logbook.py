"""Registro en memoria de los últimos eventos del servicio (SPEC-B21 RG-01).

Recibe lo mismo que la consola desde INFO, oculta tokens y correos y guarda una cantidad fija
de eventos; lo lee `GET /api/ids/logs`. No escribe en disco ni en Smartsheet. Vive en
`app.state` (PY-22): `install_logbook` lo crea y lo engancha al registro raíz.
"""

import logging
import re
import threading
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

# Cada llamada a Smartsheet se registra en INFO: llenaría el espacio; se cuenta aparte (RG-04).
_REQUEST_LOGGER = "app.smartsheet"
_SECRET = re.compile(r"(?i)bearer\s+\S+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
LEVELS = ("INFO", "WARNING", "ERROR")


@dataclass(frozen=True)
class LogEntry:
    at: str
    level: str
    source: str
    message: str


def redact(text: str) -> str:
    """Oculta tokens y correos: el registro se puede leer por HTTP (SM-01)."""
    return _EMAIL.sub("<email>", _SECRET.sub("Bearer <token>", text))


class LogBook:
    """Últimos eventos, del más viejo al más nuevo; seguro entre hilos."""

    def __init__(self, capacity: int) -> None:
        self.capacity = max(10, capacity)
        self._items: deque[LogEntry] = deque(maxlen=self.capacity)
        self._lock = threading.Lock()

    def add(self, entry: LogEntry) -> None:
        with self._lock:
            self._items.append(entry)

    def recent(
        self, level: str = "WARNING", limit: int = 100, contains: str = ""
    ) -> list[LogEntry]:
        """Del más nuevo al más viejo, desde `level`, con `contains` (sin mayúsculas)."""
        floor = logging.getLevelName(level)
        needle = contains.casefold()
        with self._lock:
            items = list(self._items)
        found = [
            e
            for e in reversed(items)
            if logging.getLevelName(e.level) >= floor and needle in e.message.casefold()
        ]
        return found[: max(0, limit)]


class LogBookHandler(logging.Handler):
    """Copia cada evento al `LogBook`, salvo las líneas INFO de cada llamada a Smartsheet."""

    def __init__(self, book: LogBook) -> None:
        super().__init__(level=logging.INFO)
        self.book = book

    def emit(self, record: logging.LogRecord) -> None:
        if record.name == _REQUEST_LOGGER and record.levelno < logging.WARNING:
            return
        try:
            message = record.getMessage()
            if record.exc_info:
                message += "\n" + logging.Formatter().formatException(record.exc_info)
            at = datetime.fromtimestamp(record.created, UTC).isoformat(timespec="seconds")
            self.book.add(LogEntry(at, record.levelname, record.name, redact(message)))
        except Exception:  # un fallo del registro nunca debe frenar al servicio (PY-16)
            self.handleError(record)


def install_logbook(capacity: int) -> LogBook:
    """Crea el registro y lo engancha al registro raíz; reemplaza uno anterior (pruebas)."""
    root = logging.getLogger()
    for handler in [h for h in root.handlers if isinstance(h, LogBookHandler)]:
        root.removeHandler(handler)
    book = LogBook(capacity)
    root.addHandler(LogBookHandler(book))
    if root.level > logging.INFO or root.level == logging.NOTSET:
        root.setLevel(logging.INFO)
    return book
