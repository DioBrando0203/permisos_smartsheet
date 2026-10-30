# future_docs

Investigaciones para posibles funciones futuras del panel. Nada de esto está implementado.

El mapa (milepost, jurisdicción de calles y parcelas) ya pasó al proyecto como PEN-29, con sus specs `backend/docs/specs/SPEC-B14-mapa.md` y `frontend/docs/specs/SPEC-11-mapa.md`; estos documentos quedan como la investigación de respaldo. OSP y JustFOIA siguen fuera de los pendientes.

## Documentos

- `OSP_MILEPOST.md`: One Stop Permitting (OSP) del FDOT; obtener County, State Road ID, Section Number y mileposts desde el paso 3 de una solicitud Utility Permit.
- `GIS_PUBLICO_FLORIDA.md`: servicios GIS públicos del FDOT y de FDACS para obtener vía, milepost, calle, condado, ciudad, ZIP y parcela de un punto o tramo, sin OSP. Verificado contra la captura de OSP.
- `MAPAS_JURISDICCION_PARCELAS.md`: mapas base gratuitos, de quién es cada calle (estatal, condado, ciudad, privada) y parcelas, con la base estatal recomendada para empezar y el detalle por condado (Broward, Palm Beach, Martin, Miami-Dade).
- `JUSTFOIA_REGISTROS_PUBLICOS.md`: portal JustFOIA del FDOT para solicitudes de registros públicos; endpoints y por qué no se automatiza el envío.
- `osp-milepost-paso3.png`: captura del paso 3 "Project Location" de OSP, que marca hasta dónde llega el alcance.

## Reglas comunes (WS-xx)

- WS-01: No evadir controles contra la automatización: captcha, detección de bots, límites de peticiones ni bloqueos. Nada de servicios que resuelven captchas ni navegadores "stealth".
- WS-02: Automatizar sólo hasta antes de enviar, publicar o cargar documentos. El envío final lo hace una persona.
- WS-03: Un formulario con autoguardado escribe en el servidor en cuanto cambia un campo, aunque nadie pulse Submit. Probar siempre con un borrador desechable.
- WS-04: Credenciales y tokens sólo en un `.env` local. Nunca en código, logs, docs, capturas, archivos HAR ni chat.
- WS-05: Antes de compartir un HAR o una captura de la pestaña Network, sanearlo: OSP manda el token también en la URL de SignalR (`bearer_token=`), no sólo en la cabecera `Authorization`.
- WS-06: Respetar `robots.txt` y sus Content-Signal; peticiones pocas y con pausas.
- WS-07: Sin datos reales de personas en docs, capturas ni ejemplos (regla general de `AGENTS.md`); usar datos sintéticos.
- WS-08: El repositorio es público en GitHub: todo lo que se guarde en esta carpeta queda publicado al hacer push.

## Registro

- 2026-10-30 10:55 (America/Lima): creada la carpeta. Análisis de JustFOIA y OSP con peticiones GET anónimas y lectura del JavaScript público de cada sitio; sin inicio de sesión y sin envíos. Estado: investigación, sin código. Evidencia: respuestas descritas en cada documento y captura `osp-milepost-paso3.png` aportada por el usuario.
- 2026-10-30 11:49 (America/Lima): servicios GIS públicos del FDOT y de FDACS consultados sin sesión. El cálculo de milepost reproduce los valores de la captura de OSP (SR 953, vía 87281000, sección 281, milepost 3.124 a 3.839). Estado: investigación verificada, sin código en el repositorio. Evidencia: `GIS_PUBLICO_FLORIDA.md` (GIS-C02).
- 2026-10-30 12:29 (America/Lima): decisión del usuario: por ahora sólo interesa el milepost, vía GIS público. Documentados los pasos para capturar un HAR de OSP (OSP-HAR-01 a OSP-HAR-12); el HAR y todo lo que exige sesión en OSP quedan en espera. Estado: documentado. Evidencia: `OSP_MILEPOST.md`.
- 2026-10-30 12:56 (America/Lima): análisis de mapas base gratuitos, jurisdicción de calles y parcelas para Broward, Palm Beach y Martin, con consultas reales sin sesión a FDOT, FDACS, Palm Beach County y Broward County. Pruebas: una vía estatal y una de condado por condado, más calles locales en Fort Lauderdale. Estado: investigación parcial; pendientes MJ-PEN-01 a MJ-PEN-07. Evidencia: `MAPAS_JURISDICCION_PARCELAS.md` (MJ-F1-03, MJ-PB-02).
- 2026-10-30 17:16 (America/Lima): el mapa pasa al proyecto como PEN-29 (SPEC-B14, SPEC-11, ADR-B16, ADR-B17 y ADR-13 del frontend, en propuesta). Estado: especificado, sin código. Evidencia: bitácoras del backend y del frontend de esa hora.
