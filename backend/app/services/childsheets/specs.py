"""Definición de cada hoja hija: qué la activa, qué se copia y qué vuelve a la maestra."""

from app.services.childsheets.rules import ROW_TYPE, ChildSpec

# Metraje que llena diseño en la maestra (SPEC-B19 FH-05, 2026-11-16); Billing lo copia siempre.
FOOTAGE = ("Total Footage", "UG", "UG + Profile", "ISP", "Aerial")
# Cantidades que siguen en la maestra y Billing copia siempre al día.
QUANTITIES = (
    "Custom MOT",
    "TYPICAL MOT",
    "Additional Site Survey",
    "Survey Certified",
    "Tone Locating",
    "Sonde FTG",
    "GPR",
)


def _records(values: dict, _child: bool) -> bool:
    """RH-03: casilla marcada o responsable asignado, y siempre con agencia (a quién se pide)."""
    wanted = values.get("Records Needed") or values.get("Records Owner")
    return bool(wanted) and bool(values.get("Agency"))


# SPEC-B18: filas con la casilla marcada o una persona asignada y con `Agency`; el trabajo vive
# en la hoja hija.
RECORDS = ChildSpec(
    name="records",
    triggers=("Records Needed", "Records Owner"),
    when=_records,
    reads=("Records Needed",),
    context=(
        "Tracking Project",
        "Linked Tracking",
        "Customer",
        "Agency",
        "Project Name",
        "Project Address",
        "City",
        "County",
        "Date Received",
        "Records Owner",
    ),
    fallback=("Linked Tracking",),
    initial=(
        "Request Type",
        "Send Method",
        "Record Request",
        "Reminder Sent",
        "LT Records",
        "Future Project #",
        "PRR #",
        "Security Key",
        "Record Received",
        "Records Status",
        "Record Box",
    ),
)

# SPEC-B19: toda fila con ID; `Designers` para la vista de diseño sobre un reporte (FH-09).
BILLING = ChildSpec(
    name="billing",
    triggers=(),
    context=(
        "Tracking Project",
        "Linked Tracking",
        "Customer",
        "Type of Project",
        "CC System",
        "Project Status",
        "Project Name",
        "Project Address",
        "City",
        "County",
        "PM Approval Date",
        "Construction Manager",
        "Agency",
        "Contractor",
        "Permit #",
        "Permit Fee",
        "Stamp And Signatures #",
        "Designers",
        *QUANTITIES,
        *FOOTAGE,
    ),
    initial=(
        "Purchase Orden",
        "Invoice? GALP",
        "Invoice? KMV",
        "Customer invoice?",
        "Invoice Completed (Galp)",
        "PM Approval Invoice Date",
        "Invoice Sent",
        "Invoice Paid",
    ),
    fallback=("Linked Tracking",),
    summary=("Invoice Status",),
    derived=(ROW_TYPE,),
)


# SPEC-B20 (PEN-54): hojas de proceso. Una hija pasa cuando tiene su tipo y su agencia y no
# nació cerrada; el contexto vacío en la hija se toma de su proyecto.
CLOSED = frozenset({"CANCELLED", "NO PERMIT REQUIRED"})
PERMIT_KINDS = frozenset({"KMV-Permit", "KMV-Line"})
PROJECT_CONTEXT = (
    "Linked Tracking",
    "Permitting Team",
    "Customer",
    "Project Name",
    "Project Address",
    "City",
    "County",
    "Designers",
    "Contractor",
    "Date Received",
    "PM Approval Date",
)
_READS = ("Type of Project", "Agency", "Project Status")


def _open(values: dict) -> bool:
    return bool(values.get("Agency")) and values.get("Project Status") not in CLOSED


def _permit(values: dict, child: bool) -> bool:
    """Hijas `Permit` y `Line` abiertas con agencia; y los proyectos `Miscellaneous` (HP-16)."""
    if not child:
        return values.get("Type of Project") == "KMV-Miscellaneous"
    return values.get("Type of Project") in PERMIT_KINDS and _open(values)


def _mot(values: dict, child: bool) -> bool:
    if not child:
        return bool(values.get("Prepare Packages"))
    return values.get("Type of Project") == "KMV-MOT" and _open(values)


PERMITS = ChildSpec(
    name="permits",
    triggers=(),
    when=_permit,
    reads=_READS,
    context=(
        "Tracking Project",
        "Type of Project",
        "Agency",
        *PROJECT_CONTEXT,
        "Design Ticket",
        "Mile Post",
    ),
    initial=("LT",),
    summary=(
        ("Permit Status", "Project Status"),
        "Permit #",
        "Permit Approved",
        "Permit Expires",
        "Permit Fee",
    ),
    fallback=(*PROJECT_CONTEXT, "Design Ticket", "Mile Post"),
    summary_children_only=True,
    # Un proyecto `Miscellaneous` recibe lo del permiso, no el estado (lo lleva la coordinación).
    mother_summary=("Permit #", "Permit Approved", "Permit Expires", "Permit Fee"),
    cancel=("Permit Status", "CANCELLED"),
)

# Filas `MOT` (hijas `KMV-MOT`) y `Package` (madres con `Prepare Packages`).
MOT = ChildSpec(
    name="mot",
    triggers=(),
    when=_mot,
    reads=(*_READS, "Prepare Packages"),
    context=("Tracking Project", "Agency", *PROJECT_CONTEXT),
    initial=("LT",),
    summary=(("MOT Status", "Project Status"), "Custom MOT", "TYPICAL MOT"),
    derived=(ROW_TYPE,),
    fallback=PROJECT_CONTEXT,
    kinds=("Package", "MOT"),
    summary_children_only=True,
    cancel=("MOT Status", "CANCELLED"),
)

# HP-14: Design Ticket y Mile Post los llena el responsable (`DT Owner`) en su hoja y vuelven a
# la fila de la maestra (el proyecto); `Permits` los toma de allí.
DESIGN_TICKETS = ChildSpec(
    name="design_tickets",
    triggers=("DT Owner",),
    context=(
        "Tracking Project",
        "Linked Tracking",
        "DT Owner",
        "Project Status",
        "Customer",
        "Project Name",
        "Project Address",
        "City",
        "County",
        "Date Received",
        "Designers",
    ),
    initial=("Design Ticket", "Mile Post"),
    summary=("Design Ticket", "Mile Post"),
)

# HP-07: datos del proyecto que una hija de la maestra toma si los tiene vacíos.
INHERITED = (
    "Customer",
    "Project Name",
    "Project Address",
    "City",
    "County",
    "CC System",
    "Date Received",
    "Survey Completed",
    "Design Completed",
    "PM Approval Date",
    "LT",
)
