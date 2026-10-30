# OSP: milepost desde una solicitud Utility Permit

Estado (2026-10-30): investigación. Nada implementado. Reglas comunes WS-xx en `README.md`.

## Objetivo

- OSP-OBJ-01: Obtener de un tramo de vía los datos que OSP calcula en el paso 3 "Project Location": County, State Road ID, Section Number, Beginning Milepost, Ending Milepost e Is Location on Turnpike.
- OSP-OBJ-02: Alcance hasta la captura `osp-milepost-paso3.png`: dibujar el tramo en el mapa y leer la fila de Work Location. Nada más: no subir documentos, no completar los pasos 4 y 5, no enviar.

## Sitio

- OSP-S01: URL `https://osp.fdot.gov/` (One Stop Permitting, FDOT).
- OSP-S02: Aplicación de una sola página en AngularJS con rutas hash: `#/ProcessType/{processTypeId}/Process/{processId}`. Usa jQuery, Breeze, SignalR 2.2 (`/signalr/hubs`) y Leaflet con Esri Leaflet para el mapa.
- OSP-S03: Código analizado: `scripts/wars-combined-internal.js?v=1792616506067` (unos 2,9 MB).
- OSP-S04: Sin captcha: el código no menciona reCAPTCHA ni otro captcha.
- OSP-S05: `robots.txt`: `User-agent: *` con `Allow: /` y `Content-Signal: search=yes,ai-train=no,use=reference`. Bloquea por nombre a bots de IA (GPTBot, ClaudeBot, CCBot y otros). El contenido no se puede usar para entrenar modelos.
- OSP-S06: Términos de uso del sitio: no revisados (ver OSP-PEN-03).

## Autenticación

- OSP-A01: OAuth2. El JavaScript renueva la sesión con `POST {base}token` y cuerpo `grant_type=refresh_token&refresh_token=…&client_id=…`. El inicio de sesión con usuario y contraseña usa el mismo endpoint; el `grant_type` exacto está por confirmar (OSP-PEN-05).
- OSP-A02: Cada llamada lleva `Authorization: Bearer {token}`. El token se guarda en el almacenamiento local del navegador con la clave `authorizationData`.
- OSP-A03: Ante un 401 la aplicación guarda `redirectAfterLogin` y lleva a `#/login`.
- OSP-A04: SignalR (`/signalr/negotiate` y `/signalr/start`) manda el token en la URL como `bearer_token=`. Ver WS-05.

## IDs conocidos

- OSP-ID01: ProcessType Utility (menú Apply For Permit > Utility): `92de6efb-0d9a-4107-b914-a76e0119f5cb`. `GET api/ProcessType/{id}` sin sesión devuelve `name: "Utility Permit"` y `processConfigurationId: a807f57f-a95d-4bde-a2d6-b2bc01299192`.
- OSP-ID02: My Permits: `d50fe1cf-4461-4899-a656-0159e1774856`.
- OSP-ID03: GIS Permit Search: `bcea6559-de4d-4d27-a8ba-015bfdc28336`.
- OSP-ID04: Permitted Locations Report (`isReportProcess: true`): `9546b82d-f919-47b5-a0bd-015c3a8a543a`. Posible fuente de lectura sin crear borradores; por revisar.
- OSP-ID05: Los IDs salen de `GET api/SiteInitialization/GetMenuItems`, que devuelve el menú completo con el `processTypeId` de cada tipo de permiso.

## Paso 3 "Project Location" (lo observado)

- OSP-P01: La solicitud es un asistente de 5 pasos. Los pasos 1, 2, 4 y 5 no se han analizado.
- OSP-P02: Sección Map: lista "Zoom To County", mapa y botón "Add Location". Se marca un punto inicial, se dibuja la línea por el trayecto y se termina con doble clic.
- OSP-P03: Sección Work Location: tabla con County, State Road ID, Section Number, Beginning Milepost, Ending Milepost e "Is Location on Turnpike?", con botones Add y Edit.
- OSP-P04: Ejemplo de la captura: Miami-Dade, SR 953, sección 281, milepost 3.124 a 3.839, fuera del Turnpike.
- OSP-P05: Debajo aparece la sección "Nearby Financial Projects" (no analizada).

## Endpoints

Sacados del JavaScript público; sólo `api/ProcessType/{id}` (200), `api/SiteInitialization/GetRoute` (200) y `api/Process/{id}` (401 sin sesión) se probaron con peticiones reales.

Lectura:
- OSP-E01: `GET api/ProcessType/{processTypeId}`: público.
- OSP-E02: `GET api/Process/{processId}`: carga la solicitud completa; requiere sesión.
- OSP-E03: `GET api/Process/{id}/ProcessName` y `GET api/Process/{id}/ProcessDataHistory/`.
- OSP-E04: `GET api/Code/GetCodes`: catálogos de listas desplegables.
- OSP-E05: `GET api/ProcessConfiguration/{id}/Statuses`: estados posibles del trámite.
- OSP-E06: Al entrar, la aplicación llama a `GetSiteConfigurationForExecution`, `GetMenuItems`, `GetEmailNotificationCount`, `GetEditableContentPages` y `GetUserGrantAuthorizations` (visto en la pestaña Network con sesión).

Mapa y milepost:
- OSP-E07: `POST api/GisDatastore/{datastoreId}/Query/{queryId}` con cuerpo `{geoJson, placeHolders}`: manda la línea dibujada como GeoJSON. Es el candidato a calcular County, vía y mileposts; por confirmar (OSP-PEN-01).
- OSP-E08: `POST api/GisDatastore/{datastoreId}/GetFeatures`.
- OSP-E09: `POST api/GisDatastore/SaveFeature`: guarda la geometría dibujada (escritura). Existe también una función `removeFeature` cuya URL no se vio.

Escritura de borrador (autoguardado, WS-03):
- OSP-E10: `POST api/Process/{id}`: guarda la solicitud entera cada vez que cambia.
- OSP-E11: `POST api/Process/{id}/Form/{formId}/{dataId}/Field/`: guarda un campo.
- OSP-E12: `POST api/Process/{id}/Form/{formId}/{dataId}/Group/{groupId}/Row/`: agrega una fila a una tabla, como Work Location. Variantes `…/Row/{rowId}/Delete`, `…/Row/{rowId}/SaveMultiAddFields` y `…/Row/{rowId}/Property/`.
- OSP-E13: `POST api/Process/{id}/Calculate/`.
- OSP-E14: `api/document/process/…`: documentos; fuera de alcance.

Límite:
- OSP-E15: `api/Process/{id}/ExecuteUserAction/{actionId}` y `…/ExecuteUserActionWithModel/`: ejecutan los botones del trámite, incluido el envío. No se sabe aún si "siguiente paso" también pasa por aquí (OSP-PEN-02).

No tocar (administración del FDOT):
- OSP-E16: `api/developer/*`, `api/Workflow/WorkflowBlock/*`, `POST api/ProcessConfiguration/*` y `api/ContentManagement/*`.

## Enfoques posibles

- OSP-ENF-01 (para empezar): Playwright con navegador visible y sesión iniciada por una persona. El script abre un borrador de prueba, dibuja el tramo o reutiliza uno, lee la fila de Work Location y se detiene. Dibujar en el mapa exige convertir coordenadas a píxeles y simular clics; frágil, pero no depende de detalles internos.
- OSP-ENF-02: Llamar directo a OSP-E07 con el GeoJSON del tramo y el token de la sesión. Sería más estable y quizá no agregue filas al borrador. Antes hay que confirmar con un HAR los IDs, el formato de la respuesta y que la consulta no escribe.
- OSP-ENF-03 (por verificar): Buscar un servicio GIS público del FDOT que dé el milepost de una geometría, para no pasar por OSP ni crear borradores. No verificado.

## Reglas propias (OSP-R)

- OSP-R01: Nunca ejecutar la acción de envío (OSP-E15) ni subir documentos (OSP-E14).
- OSP-R02: Cada cambio en el mapa, en un campo o en una fila queda guardado en el servidor del FDOT: usar un borrador de prueba dedicado y no tocar solicitudes reales.
- OSP-R03: No llamar a los endpoints de OSP-E16, aunque aparezcan en el código.

## Pendientes (OSP-PEN)

- OSP-PEN-01: HAR saneado (WS-05) de una sesión en el paso 3 mientras se dibuja un tramo, para confirmar qué llamada calcula el milepost, sus `datastoreId` y `queryId`, el formato de la respuesta y si escribe algo.
- OSP-PEN-02: Ver cómo se avanza entre pasos e identificar el `actionId` del envío, para bloquearlo.
- OSP-PEN-03: Revisar los términos de uso de OSP sobre acceso automatizado.
- OSP-PEN-04: Investigar OSP-ENF-03.
- OSP-PEN-05: Confirmar el `grant_type` del inicio de sesión.
