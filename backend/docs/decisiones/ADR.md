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
