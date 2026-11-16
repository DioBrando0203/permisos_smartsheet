# Servicio GIS: primera etapa

- Estado: copia de transición independiente del backend de Smartsheet. El panel todavía usa el backend anterior; no hay cambio de tráfico ni traslado del frontend.
- Alcance: mapa, fuentes GIS públicas, trazos, jurisdicción y orientación sobre permisos viales. Los permisos de acceso a hojas permanecen en Smartsheet.
- Contrato: las rutas `/api/map` mantienen SPEC-B14. No lee `backend/.env`, no necesita el token ni ejecuta el ID Manager.
- Arranque local desde esta carpeta: instalar el proyecto y ejecutar `uvicorn app.main:app --host 127.0.0.1 --port 8711`. Puerto provisional; `/docs` muestra las rutas.
- Pruebas desde esta carpeta: `../../backend/.venv/bin/python -m pytest tests`. No llaman a fuentes externas.
- Siguiente etapa: mover la interfaz y sus pruebas, configurar el encaminamiento, verificar el contrato y retirar la copia anterior sólo después de validar la transición. Mientras existan dos copias, cualquier corrección GIS debe aplicarse en ambas.
