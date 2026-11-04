
import psycopg
from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.services.ids.cli import DSN


router = APIRouter()

@router.get("/status", summary="Consultar estado del ID Manager")
def get_ids_status():
    """COnsulta la configuracion sin modificar datos"""

    settings = get_settings()

    return{ 
        "service": "GALP ID Manager",
        "read_only": settings.app_read_only,
        "automatic_generation_enabled": False,
        "smartsheet_writes_enabled": False,
        "database_checked": False,
        "message": "Servicio en fase de integracion. Postgresql aun no verfica desde este endpoint"
    }


import psycopg
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.services.ids.cli import DSN


router = APIRouter()

@router.get("/status", summary="Consultar estado del ID Manager")
def get_ids_status():
    """Consulta la configuracion sin modificar datos"""

    settings = get_settings()

    return { 
        "service": "GALP ID Manager",
        "read_only": settings.app_read_only,
        "automatic_generation_enabled": False,
        "smartsheet_writes_enabled": False,
        "database_checked": False,
        "message": "Servicio en fase de integracion. Postgresql aun no verfica desde este endpoint"
    }


@router.get("/database")
def get_ids_database():
    try:
        with psycopg.connect(
            DSN,
            connect_timeout=5,
            options="-c default_transaction_read_only=on",
        ) as conn:
            total_ids = conn.execute(
                "SELECT COUNT(*) FROM asignacion_id"
            ).fetchone()[0]

            confirmed_ids = conn.execute(
                "SELECT COUNT(*) FROM asignacion_id WHERE estado = 'confirmado'"
            ).fetchone()[0]

            total_sequences = conn.execute(
                "SELECT COUNT(*) FROM secuencia_id"
            ).fetchone()[0]

            total_events = conn.execute(
                "SELECT COUNT(*) FROM auditoria_id"
            ).fetchone()[0]

        return {
            "status": "success",
            "total_ids": total_ids,
            "confirmed_ids": confirmed_ids,
            "total_sequences": total_sequences,
            "total_events": total_events
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar la base de datos: {str(e)}"
        )
        

    @router.get("/assignments")
    def get_id_assignments(
        limit: int = Query(default=25, ge=1, le=100)
    ):