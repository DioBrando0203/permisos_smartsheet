"""Registro en memoria del servicio (SPEC-B21 RG-01, CA-B21-01); datos sintéticos."""

import logging

from app.core.logbook import LogBook, LogBookHandler, LogEntry, install_logbook, redact


def test_tokens_and_emails_are_hidden() -> None:
    assert redact("Bearer abc.123 de persona1@example.com") == "Bearer <token> de <email>"


def test_keeps_the_newest_up_to_capacity_and_filters_by_level_and_text() -> None:
    book = LogBook(10)
    for n in range(12):
        book.add(LogEntry(f"t{n}", "ERROR" if n % 2 else "INFO", "app.x", f"Paso {n}"))
    everything = book.recent("INFO", 100)
    assert len(everything) == 10 and everything[0].message == "Paso 11"
    assert {e.level for e in book.recent("ERROR", 100)} == {"ERROR"}
    assert [e.message for e in book.recent("INFO", 100, "paso 3")] == ["Paso 3"]
    assert len(book.recent("INFO", 2)) == 2


def test_request_lines_stay_out_and_errors_keep_their_trace() -> None:
    book = install_logbook(50)
    requests = logging.getLogger("app.smartsheet")
    requests.info("smartsheet GET /sheets/1 -> 200 (5 ms)")
    requests.warning("smartsheet GET /sheets/1 -> error de red")
    try:
        raise ValueError("falla sintética")
    except ValueError:
        logging.getLogger("app.services.ids.monitor").exception("ciclo: falló el paso records")
    found = book.recent("INFO", 10)
    assert [e.source for e in found] == ["app.services.ids.monitor", "app.smartsheet"]
    assert found[0].level == "ERROR" and "ValueError: falla sintética" in found[0].message


def test_installing_again_replaces_the_previous_handler() -> None:
    install_logbook(20)
    install_logbook(20)
    handlers = [h for h in logging.getLogger().handlers if isinstance(h, LogBookHandler)]
    assert len(handlers) == 1
