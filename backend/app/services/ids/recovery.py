"""Recuperación de operaciones incompletas: decide qué hacer con cada reserva; no escribe."""

# Acción del DRY_RUN para una fila reservada -> paso que retoma el procesador sin reservar otra vez.
_RECOVERY = {
    "confirm_reservation": "confirm",  # el Stable ID ya coincide: sólo falta confirmar
    "would_write": "write",  # Stable ID vacío: se escribe la misma reserva
    "pending_formula": "write",
    "pending_parent": "wait_parent",  # se retoma cuando el padre esté confirmado
    "renumber_copy": "write",  # copia de una madre: se escribe la misma reserva
}


def plan_recovery(reserved: list[tuple[int, int, str]], report: dict) -> list[dict]:
    """Cruza reservas sin confirmar con el estado actual de las hojas.

    Una fila ausente o vaciada queda `row_missing`: su número nunca se reutiliza y requiere
    revisión humana; un conflicto nunca se sobrescribe.
    """
    rows = {
        (item["sheet_id"], item["row_id"]): item for item in report["pending_or_conflicting_rows"]
    }
    plan = []
    for sheet_id, row_id, value in reserved:
        item = rows.get((str(sheet_id), str(row_id)))
        action = item["action"] if item else None
        plan.append(
            {
                "sheet_id": str(sheet_id),
                "row_id": str(row_id),
                "reserved_id": value,
                "current_action": action,
                "stable_id": item.get("stable_id") if item else None,
                "recovery": _RECOVERY.get(action, "manual_review") if item else "row_missing",
            }
        )
    return plan
