# JustFOIA (FDOT): solicitudes de registros públicos

Estado (2026-10-30): investigación. Conclusión: el envío no se automatiza (WS-01). Reglas comunes WS-xx en `README.md`.

## Sitio

- JF-S01: Portal `https://fdot.justfoia.com/publicportal/home/newrequest`; formulario `https://fdot.justfoia.com/Forms/Launch/d705cbd6-1396-49b7-939e-8d86c5a87deb` (formId `d705cbd6-1396-49b7-939e-8d86c5a87deb`).
- JF-S02: Aplicación Vue 2 con Vuetify, empaquetada con Vite (`/dist/MainApp.*.js`, `/dist/Launch.*.js`, `/dist/ReCaptchaVuePlugin.*.js`).
- JF-S03: La captura del formulario que se analizó no se guardó: contenía datos reales de una persona (WS-07).

## Endpoints

- JF-E01: `GET /api/Forms/{formId}`: configuración. `FormName: "Public Records Request"`, `TotalAllowableFiles: 5`, `DueDateType: "Business Days"`, `TimeZone: "Eastern Standard Time"`.
- JF-E02: `GET /api/Forms/{formId}/Fields?lang=`: lista de los 19 campos con nombre, tipo, obligatoriedad, opciones y expresiones de visibilidad.
- JF-E03: `GET /api/Attachments/GetValidFileExtensions`: extensiones permitidas para adjuntos.
- JF-E04: `POST /api/Forms/{formId}`: envío. El cuerpo son los datos del formulario más `TotalAttachments` y `RecaptchaResponse`.
- JF-E05: `POST /api/Attachments/{id}/TransferAttachment`: asocia adjuntos a la solicitud. La subida del archivo en sí no se identificó.
- JF-E06: El parámetro `_=` de las URL es sólo un número para evitar la caché; no hace falta.

## Campos (JF-E02)

- JF-C01: Datos de contacto, todos opcionales: `FirstName`, `LastName`, `Phone`, `Email`, `Address`, `City`, `State`, `Zip`.
- JF-C02: `Description` (texto largo): obligatorio.
- JF-C03: `DeliveryMethod`: obligatorio; `None`, `PickUp` o `Mail`.
- JF-C04: `RequestorType`: `Yourself`, `MediaOutlet`, `BusinessLegalFirm`, `ElectedOfficial` o `PublicAgency`.
- JF-C05: `OrganizationName`: visible si `RequestorType` es `BusinessLegalFirm` o `MediaOutlet`. `OfficialName`: visible si es `ElectedOfficial`.
- JF-C06: `ConfidentialInfoWarning`: aviso que aparece si la descripción menciona fecha de nacimiento, seguro social, licencia de conducir o tarjeta de crédito.
- JF-C07: El resto son etiquetas, logotipo y un campo `RequestDescriptionMainRequired` condicionado a `RequestDescriptionRequiredCheck`.

## Protección del envío

- JF-P01: El envío exige un token de reCAPTCHA v3 (acción `submit_request`) en `RecaptchaResponse`, generado por el navegador al pulsar Submit.
- JF-P02: Si el servidor responde `RequiresV2Challenge`, aparece el reCAPTCHA de casilla y su resultado va en `RecaptchaV2Response`.
- JF-P03: Sin token válido el servidor rechaza con "We couldn't verify your submission".
- JF-P04: Un navegador controlado por Playwright suele sacar puntuación baja en v3 y termina en el reto v2. Hacerlo pasar solo sería evadir el control (WS-01).

## Opciones válidas

- JF-O01: Envío asistido con Playwright: navegador visible, el script rellena los campos y adjuntos y se detiene; una persona resuelve el captcha si aparece y pulsa Submit; el script lee la confirmación y guarda el número de solicitud.
- JF-O02: Solicitud por correo al custodio de registros públicos del FDOT. La ley de Florida (capítulo 119) no obliga a usar el portal y el propio formulario dice que se puede pedir por varios medios. Correo exacto pendiente (JF-PEN-01).
- JF-O03: Seguimiento leyendo los correos de confirmación y avance que manda JustFOIA.
- JF-O04: Preguntar al FDOT o a JustFOIA por un canal oficial para solicitudes frecuentes.

## Pendientes (JF-PEN)

- JF-PEN-01: Obtener de la página oficial del FDOT el correo del custodio de registros públicos.
- JF-PEN-02: Si se usan adjuntos en JF-O01, identificar el endpoint de subida.
