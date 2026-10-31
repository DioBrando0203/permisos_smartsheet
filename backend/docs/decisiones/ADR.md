# Decisiones de arquitectura (backend)

Formato: contexto, decisión, consecuencias. Una decisión sólo se reemplaza con otra que la cite.

## ADR-B01 Backend intermediario con el token en el servidor

Fecha: 2026-10-12. Estado: vigente.
Contexto: el token es de un administrador del sistema de la cuenta; quien lo tenga puede leer y cambiar cualquier hoja.
Decisión: sólo el backend conoce el token (`SMARTSHEET_ACCESS_TOKEN` en `backend/.env`, `SecretStr` en `Settings`). El navegador habla con el backend, nunca con Smartsheet.
Consecuencias: un único punto de control para reglas, reintentos y caché; el frontend no necesita CORS con Smartsheet. El token debe rotarse si se filtra (Smartsheet, Personal Settings, API Access).

## ADR-B02 Smartsheet como única fuente de verdad, sin base de datos

Fecha: 2026-10-12. Estado: vigente.
Contexto: los permisos cambian también desde Smartsheet; una copia propia quedaría desfasada.
Decisión: sin base de datos. Toda lectura viene de Smartsheet (con caché corta, ADR-B06) y toda escritura se confirma releyendo de Smartsheet.
Consecuencias: sin migraciones ni sincronización; la vista por usuario cuesta una solicitud por hoja (ADR-B09). Un historial propio exigiría un ADR nuevo (PEN-09).

## ADR-B03 Endpoints unificados `/2.0/shares`

Fecha: 2026-10-12. Estado: vigente; escrituras pendientes de verificar (PEN-07).
Contexto: Smartsheet ofrece los endpoints por recurso (`/sheets/{id}/shares`) y los unificados (`/shares?assetType=sheet&assetId=…`), que son la dirección actual de su API. El 2026-10-12 ambos respondieron igual en lectura con esta cuenta; el unificado devuelve `items` y pagina con `lastKey`, y acepta `sharingInclude=ITEM,WORKSPACE`.
Decisión: usar los unificados para listar, leer, crear (`POST`), cambiar (`PATCH`) y quitar (`DELETE`). Los legados quedan como respaldo sólo si la verificación de PEN-07 falla, y ese cambio se registra aquí.
Consecuencias: el mismo cliente servirá para workspaces (`assetType=workspace`, PEN-10). Los ids de usuario y grupo llegan como texto.

## ADR-B04 Propietario intocable desde el panel

Fecha: 2026-10-12. Estado: vigente.
Contexto: en Smartsheet, dar `OWNER` transfiere la propiedad y quitar al propietario no es posible o deja la hoja en un estado difícil de recuperar.
Decisión: el backend rechaza crear o cambiar a `OWNER` (`OWNER_NOT_ASSIGNABLE`) y cambiar o quitar el permiso del propietario (`OWNER_LOCKED`), antes de llamar a Smartsheet.
Consecuencias: transferir propiedad se hace en Smartsheet. El panel muestra al propietario como bloqueado.

## ADR-B05 Permisos heredados de sólo lectura

Fecha: 2026-10-12. Estado: vigente.
Contexto: un permiso con `scope=WORKSPACE` se hereda del workspace; borrarlo o cambiarlo desde la hoja no aplica o afecta a todas las hojas del workspace.
Decisión: se muestran con `locked_reason=INHERITED` y el backend rechaza cambiarlos o quitarlos desde la hoja (`SHARE_INHERITED`).
Consecuencias: para corregirlos hará falta administrar workspaces (PEN-10).

## ADR-B06 Caché en memoria con vencimiento e invalidación

Fecha: 2026-10-12. Estado: vigente.
Contexto: Smartsheet limita a 300 solicitudes por minuto por token y la vista por usuario lee todas las hojas.
Decisión: `TtlCache` en memoria del proceso (120 s por defecto), invalidada al escribir y con `refresh=true` para forzar lectura. Lecturas simultáneas de la misma clave comparten una llamada. Las escrituras siempre leen el permiso actual sin caché antes de decidir.
Consecuencias: un cambio hecho en Smartsheet puede tardar hasta el vencimiento en verse; el panel ofrece "Actualizar". Con varios procesos (workers de Uvicorn) cada uno tendría su caché: se ejecuta con un solo proceso.

## ADR-B07 Identificadores de Smartsheet como texto en el contrato

Fecha: 2026-10-12. Estado: vigente.
Contexto: los ids de hoja tienen hasta 16 dígitos (el mayor visto, `7990647450455940`) y están cerca de `Number.MAX_SAFE_INTEGER` (9007199254740991); Smartsheet no garantiza que no lo superen y JavaScript redondearía en silencio. Smartsheet ya entrega los ids de usuario y grupo de `/shares` como texto.
Decisión: todo id viaja como texto en el contrato (`sheet_id`, `user_id`, `group_id`, `share_id`). Las rutas aceptan el id como texto de dígitos.
Consecuencias: el frontend nunca convierte ids a número.

## ADR-B08 Local por defecto, red local explícita

Fecha: 2026-10-12. Estado: vigente.
Contexto: sin login (PEN-08), cualquiera que abra el panel actúa como administrador de la cuenta.
Decisión: Uvicorn en 127.0.0.1; Host y Origin permitidos desde `APP_ALLOWED_HOSTS` y `APP_ALLOWED_ORIGINS`; las escrituras con Origin fuera de la lista reciben 403 (`OriginMiddleware`).
Consecuencias: abrirlo en la red exige configurarlo a propósito y asumir que todos en esa red pueden cambiar permisos hasta que exista PEN-08.

## ADR-B09 Vista por usuario por agregación

Fecha: 2026-10-12. Estado: vigente.
Contexto: la API de Smartsheet no tiene un endpoint "hojas compartidas con esta persona" para cualquier usuario.
Decisión: leer los permisos de todas las hojas con concurrencia acotada y caché, y agrupar por persona o grupo. Fallos por hoja no detienen el resto (`incomplete`).
Consecuencias: primera carga lenta con muchas hojas (unas 100 solicitudes hoy); se mide en RESULTADOS. Si crece mucho, evaluar precarga en segundo plano.

## ADR-B10 Directorio unificado de personas

Fecha: 2026-10-12. Estado: vigente.
Contexto: el usuario pensaba que `/contacts` era la gente con acceso. El cruce real mostró que no: 44 contactos, 36 personas con acceso, 13 contactos sin acceso y 5 con acceso fuera de contactos. La API de contactos es de sólo lectura.
Decisión: `GET /api/users` une contactos, usuarios de la organización y personas o grupos con permisos, por correo, marcando su origen (`is_contact`, `is_org_member`) y con `sheet_count` 0 cuando no tiene acceso. Dar acceso a cualquiera de ellos es crear un permiso en la hoja (SPEC-B02).
Consecuencias: un solo lugar para buscar a quién dar acceso. Crear usuarios de la organización queda aparte (PEN-13).

## ADR-B11 Modo solo lectura por defecto

Fecha: 2026-10-12. Estado: vigente.
Contexto: el token es de administrador y el usuario quiere revisar sin cambiar nada todavía, aunque con el CRUD listo.
Decisión: `APP_READ_ONLY` (por defecto `true`) bloquea en `ShareService` toda escritura con 403 `READ_ONLY_MODE` antes de leer o escribir en Smartsheet. `GET /api/health` informa el modo para que el frontend oculte o deshabilite las acciones.
Consecuencias: escribir exige editar `backend/.env` y reiniciar a propósito. Las pruebas de escritura usan `app_read_only=False` con Smartsheet simulado.

## ADR-B12 Auditoría con tabla de reglas y dominios personales

Fecha: 2026-10-12. Estado: vigente.
Contexto: en el plan Crown Castle 2026, 17 de 30 accesos son correos @hotmail.com con edición y 3 externos pueden compartir. El usuario quiere ver esto sin revisar fila por fila.
Decisión: `audit_rules.RULES` es una tabla de reglas puras con código, severidad y mensaje; `PERSONAL_DOMAINS` es una lista cerrada de dominios personales. "Externo" significa no estar en `GET /2.0/users`; si esa lista no se puede leer, no se emiten alertas de externos (`org_known=false`). El propietario nunca genera alertas.
Consecuencias: una regla nueva es una entrada en la tabla. En esta cuenta casi todos son "externos" porque la organización tiene 4 usuarios con licencia: la alerta importante es `EXTERNAL_CAN_SHARE`, no el conteo de externos.

## ADR-B13 Operaciones masivas con simulación por defecto

Fecha: 2026-10-12. Estado: vigente.
Contexto: copiar permisos o quitar a alguien de muchas hojas afecta a decenas de accesos de una vez y Smartsheet no permite deshacer.
Decisión: `dry_run=true` por defecto; la simulación devuelve cada paso (`CREATE`, `UPGRADE`, `KEEP`, `SKIP`, `REMOVE`) y funciona en modo solo lectura. Ejecutar exige `dry_run=false` y `APP_READ_ONLY=false`, reutiliza `ShareService` paso a paso (mismas reglas e invalidación) y aísla los fallos. Copiar nunca baja ni quita; `OWNER` se copia como `ADMIN`.
Consecuencias: el usuario ve exactamente qué pasaría antes de ejecutar. Ejecutar muchos pasos consume solicitudes de Smartsheet (límite de 300 por minuto); el cliente ya reintenta ante 429.

## ADR-B14 Arranque con un comando y puerto libre de respaldo

Fecha: 2026-10-16. Estado: vigente. Amplía ADR-B08.
Contexto: el usuario quiere levantar el backend sin escribir el puerto y que no choque con otros proyectos.
Decisión: desde `backend/` con el entorno activado, `python run.py` ejecuta `app.launcher`: usa 8710 si está libre y, si no, uno que asigna el sistema; lo imprime y lo pasa como `APP_PORT`. `Settings.allowed_origins` agrega `http://127.0.0.1:<puerto>` y `http://localhost:<puerto>` para que Swagger pueda escribir desde ese mismo origen.
Consecuencias: con el puerto de respaldo cambia la dirección en cada arranque; el frontend (PEN-06) deberá leer el puerto real en vez de suponer 8710. Hay una ventana mínima entre comprobar el puerto y que Uvicorn lo ocupe; si otro proceso lo toma justo entonces, Uvicorn falla y basta con volver a iniciar.

## ADR-B15 Complementar, nunca reemplazar

Fecha: 2026-10-16. Estado: vigente. Decisión del usuario.
Contexto: se evaluaron Jira y Salesforce por sus conectores de pago y la posibilidad de construir servicios propios.
Decisión: el proyecto no reemplaza ninguna herramienta. Cada función nueva debe cumplir una de dos: (a) Smartsheet no la tiene (por ejemplo, auditoría de permisos, comparación de hojas, alertas, accesos con vencimiento), o (b) Smartsheet la tiene pero aquí es claramente mejor o más rápida (por ejemplo, quitar a alguien de muchas hojas, ver la actividad de una hoja). Y siempre: no entorpecer el trabajo actual; la gente sigue trabajando en Smartsheet, que es la fuente de verdad; nada se duplica ni obliga a migrar.
Consecuencias: se descartan reemplazar Jira (tableros, flujos completos) y un CRM. Antes de cada PEN nuevo se anota en su descripción si es (a) o (b) y por qué no entorpece. PEN-24 se rige por esta decisión.

## ADR-B16 Mapa como módulo del mismo backend, en Python

Fecha: 2026-10-30. Estado: vigente. Aprobada por el usuario al solicitar la implementación de PEN-29.
Contexto: el usuario quiere un mapa con vía, milepost, jurisdicción y parcela, consumido por el mismo frontend desde una entrada nueva de la navegación. Los datos salen de servicios GIS públicos (FDOT y FDACS) que aceptan CORS. Se evaluaron tres opciones: que el navegador llame directo a esos servicios, un servicio aparte o un módulo dentro de este backend.
Decisión: módulo nuevo dentro de este backend FastAPI, en Python, aislado como `services/smartsheet/`: transporte y cliente propios en `services/gis/`, reglas puras en `services/map_rules.py`, caso de uso en `services/map.py` y ruta `api/routes/map.py` bajo `/api/map/...` (SPEC-B14). El módulo GIS no importa nada de Smartsheet ni al revés.
Motivos:
- Reutiliza lo que ya existe y está probado: arranque con `run.py` y puerto propio (ADR-B14), proxy del frontend (ADR-07 del frontend), `TtlCache`, errores con código, configuración, `respx` en pruebas y acceso local por defecto (ADR-B08).
- El frontend sigue hablando sólo con su backend: un único contrato normalizado aunque cada condado publique sus datos con formato distinto.
- El milepost y la jurisdicción son cálculos puros que se prueban con pytest sin red, igual que las reglas de permisos.
- Un servicio aparte duplicaría arranque, puerto, CORS, configuración y pruebas para un volumen interno pequeño de sólo lectura.
Condiciones:
- Transporte HTTP propio, sin cabecera de autorización: el token de Smartsheet nunca viaja a un servicio GIS (SPEC-B14, CA-08).
- Caché de una hora por defecto (`gis_cache_ttl_seconds`), excepción documentada a la caché corta de ADR-B06: los datos GIS públicos cambian una vez al año y no hay escrituras propias que invaliden.
- Sólo lectura: `APP_READ_ONLY` no lo afecta y el mapa no escribe en Smartsheet.
- `APP_GIS_ENABLED=false` lo apaga sin tocar el resto del panel.
Consecuencias: un fallo de los servicios GIS degrada sólo el mapa (respuesta parcial o 502 `GIS_UNAVAILABLE`), no las vistas de permisos. Si algún día lo consumen otros sistemas o crece mucho el volumen, el módulo se puede extraer a un servicio propio porque no comparte código de dominio.

## ADR-B17 Fuentes GIS públicas y datos de propietarios

Fecha: 2026-10-30. Estado: vigente. Aprobada por el usuario al solicitar la implementación de PEN-29.
Contexto: no hay una sola fuente con todo. La base estatal (FDOT para vías, milepost y límites; FDACS para parcelas) cubre igual a todos los condados; los condados publican más detalle con formatos distintos (`future_docs/MAPAS_JURISDICCION_PARCELAS.md`). Las parcelas traen el nombre del propietario, que en Florida es registro público.
Decisión:
- Fase base: sólo FDOT y FDACS. Los adaptadores de condado (Palm Beach primero, por su campo `RESP_AUTH`) se agregan después, uno por uno, sin cambiar el contrato: sólo suben la confianza de la jurisdicción.
- Sólo GET a URL públicas y documentadas, con pocas solicitudes, plazos y caché; nunca saltar un control de acceso ni un servicio que pida token.
- `owner_name` se devuelve para mostrarlo, pero no se registra en logs ni mensajes de error, no se guarda en disco y en pruebas, fixtures y docs sólo hay nombres sintéticos (igual que los correos de Smartsheet).
- Cada respuesta dice de qué fuente salió cada dato y si alguna falló, para que nadie tome una aproximación por un dato oficial.
Consecuencias: la jurisdicción de calles locales es una aproximación con confianza baja hasta tener el adaptador de su condado. El mapa no sustituye la consulta oficial en OSP ni en el condado antes de pedir un permiso.
Ampliaciones (2026-10-30), con las mismas reglas (GET público, sin clave, plazos, caché y fuente declarada):
- Buscador: geocodificador del Censo de EE. UU. (SPEC-B14 punto 9); agregado en el commit "mapa mejorado", pendiente de confirmación explícita del usuario.
- Respaldo de parcelas de Broward (capa pública del condado, sólo `FOLIO`) cuando FDACS falla, a pedido del usuario tras quedar FDACS inaccesible (PEN-30, B-13). Condiciones de uso por revisar (MJ-PEN-06).
