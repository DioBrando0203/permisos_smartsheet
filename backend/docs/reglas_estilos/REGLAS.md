# Reglas de estilo (Python)

- ES-01: identificadores en inglés; mensajes al usuario, docstrings y comentarios en español.
- ES-02: Ruff es la autoridad: líneas de 100 caracteres, imports ordenados (`I`), modernización (`UP`), bugbear (`B`) y async (`ASYNC`).
- ES-03: nombres por intención: verbos para funciones (`list_sheet_shares`), sustantivos para datos (`RawShare`), `is_`/`has_`/`can_` para booleanos.
- ES-04: constantes en MAYÚSCULAS al inicio del módulo; privadas con `_`.
- ES-05: orden dentro de un módulo: docstring, imports, constantes, tipos, función pública principal, funciones privadas en orden de uso.
- ES-06: mensajes de error con causa y acción posible: "Smartsheet está limitando las solicitudes. Espere un minuto e inténtelo de nuevo."
- ES-07: códigos de error en MAYÚSCULAS con guion bajo y estables (`SHARE_INHERITED`); el frontend decide el texto con el código, no con el mensaje.
- ES-08: sin código comentado ni `print`; sin TODO sin registrar en bloqueos o pendientes.
- ES-09: rutas HTTP en inglés, minúsculas y sustantivos en plural (`/sheets/{sheet_id}/shares`).
