"""Definición de cada hoja hija: qué la activa, qué se copia y qué vuelve a la maestra."""

from app.services.childsheets.rules import ROW_TYPE, ChildSpec

# Metraje que llena diseño: vive en Billing; la maestra sólo lo da al crear la fila.
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

# SPEC-B18: filas con la casilla marcada o una persona asignada; el trabajo vive en la hoja hija.
RECORDS = ChildSpec(
    name="records",
    triggers=("Records Needed", "Records Owner"),
    context=(
        "Tracking Project",
        "Customer",
        "Agency",
        "Project Name",
        "Project Address",
        "City",
        "County",
        "Date Received",
        "Records Owner",
    ),
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
    ),
    initial=(
        *FOOTAGE,
        "Purchase Orden",
        "Invoice? GALP",
        "Invoice? KMV",
        "Customer invoice?",
        "Invoice Completed (Galp)",
        "PM Approval Invoice Date",
        "Invoice Sent",
        "Invoice Paid",
    ),
    summary=("Invoice Status",),
    derived=(ROW_TYPE,),
)
