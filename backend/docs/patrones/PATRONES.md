# Patrones de diseño (backend)

Catálogo de patrones a usar: dónde, cuándo aplicarlos y cuándo no. Antes de crear una estructura nueva, reutilizar una de estas.

## Gateway (cliente de servicio externo)

Dónde: `services/smartsheet/client.py` (`SmartsheetClient`).
Qué: un objeto concentra autenticación, reintentos, paginación, concurrencia y traducción de errores de Smartsheet.
Regla: SM-02. Los servicios piden datos con métodos con nombre (`list_sheet_shares`), nunca rutas sueltas.

## Anti-corruption layer (mapeo)

Dónde: `services/smartsheet/mappers.py`.
Qué: el JSON de Smartsheet (camelCase, ids mixtos, campos opcionales) se convierte en dataclasses propias en un solo lugar.
Cuándo: todo dato que entra desde Smartsheet. Si Smartsheet cambia, sólo cambia este módulo.

## Servicio de dominio (casos de uso)

Dónde: `services/sheets.py`, `shares.py`, `users.py`.
Qué: orquestan cliente, caché y reglas; no conocen HTTP de FastAPI ni JSON de Smartsheet.
Regla: las rutas sólo validan, llaman a un método del servicio y responden.

## Reglas puras (Specification)

Dónde: `services/permissions/rules.py` (`can_edit_share`, `validate_new_share`, `lock_reason`).
Qué: cada decisión de permiso es una función pura que devuelve permitido o un `LockedReason`/código de error.
Cuándo: toda condición sobre propietario, heredado, niveles o capacidad del token. Nunca repetir esas condiciones en rutas o servicios.

## Tabla de niveles

Dónde: `services/permissions/levels.py`.
Qué: `AccessLevel` con su orden (`rank`), si es asignable y su etiqueta en español en un solo mapa.
Cuándo: ordenar, comparar ("nivel más alto") o mostrar niveles. Prohibido `if level == "EDITOR" or ...` disperso.

## Inyección de dependencias de FastAPI

Dónde: `api/deps.py`.
Qué: cliente, caché, configuración y servicios se obtienen con `Depends`; las pruebas los sustituyen con `app.dependency_overrides`.

## Cache-aside con single flight

Dónde: `services/cache.py` usado desde los servicios de dominio.
Qué: el servicio pide la clave; si falta, la carga una sola vez aunque haya solicitudes simultáneas; las escrituras invalidan.
Cuándo: lecturas repetidas a Smartsheet. Nunca para decidir una escritura (SM-06 usa datos frescos).

## Reintento con espera exponencial

Dónde: `client._request`.
Qué: reintentos acotados con espera creciente y variación aleatoria, respetando `Retry-After`.
Regla: SM-04 (escrituras sólo ante 429 y 503).

## Tolerancia por elemento (Bulkhead)

Dónde: `users.py` al recorrer hojas.
Qué: una hoja que falla se anota en `failed_sheets` y no detiene el resto.

## Releer después de escribir

Dónde: `shares.py`.
Qué: la respuesta de una escritura se arma releyendo de Smartsheet, no suponiendo el resultado.

## Antipatrones prohibidos

- Módulos `utils.py` o `helpers.py` genéricos.
- Rutas que llaman a `httpx` o contienen reglas de permisos.
- Devolver o reenviar JSON crudo de Smartsheet.
- Comparar niveles como texto o por posición en listas sueltas.
- Caché global a nivel de módulo (impide pruebas aisladas).
- Reintentar escrituras ante 500 (puede duplicar un permiso o un correo de aviso).
- Capturar `Exception` para ocultar errores de programación.
