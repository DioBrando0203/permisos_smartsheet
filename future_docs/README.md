# future_docs

Investigaciones para posibles funciones futuras, fuera del alcance actual del panel de permisos de Smartsheet. Nada de esto está implementado ni forma parte de los pendientes PEN-xx de `backend/docs/REQUERIMIENTOS.md`.

## Documentos

- `OSP_MILEPOST.md`: One Stop Permitting (OSP) del FDOT; obtener County, State Road ID, Section Number y mileposts desde el paso 3 de una solicitud Utility Permit.
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
