# SPEC-B10 Salud de las automatizaciones

Estado: implementada
Código: `api/routes/automations.py`, `services/automations.py`, `services/automation_rules.py`
Relacionadas: SPEC-B02, ADR-B15, PEN-25

## Objetivo

Mostrar qué alertas y flujos de Smartsheet no funcionan y por qué, para arreglarlos a mano en Smartsheet. Tipo (ADR-B15): Smartsheet no avisa que sus automatizaciones están apagadas o no pueden notificar a nadie; el panel no cambia nada.

## Fuente verificada (2026-10-16)

- `GET /2.0/sheets/{id}/automationrules?pageSize&page`: regla con `id`, `name`, `enabled`, `disabledReason`, `disabledReasonText`, `createdAt`, `createdBy`, `modifiedAt`, `modifiedBy`, `userCanModify` y `action` (`type`, `frequency`, `recipients` con `email`, `recipientColumnIds`, `notifyAllSharedUsers`, `subject`, `message`, `includedColumnIds`…).
- Cuenta real: 80 reglas en 63 de 110 hojas; 71 apagadas (56 a mano, 15 por `NO_POTENTIAL_RECIPIENTS`, cuyo texto dice que no hay destinatarios que puedan recibir avisos según los permisos de la hoja o la lista de dominios aprobados); 16 sin destinatarios; 2 avisan a columnas de texto. Ninguna usa las columnas de diseñador.

## Comportamiento

1. `GET /api/sheets/{sheet_id}/automations`: reglas de la hoja con diagnóstico.
2. `GET /api/automations?q=&only_problems=&refresh=`: todas las hojas del token (las de otras personas no se pueden abrir), con totales; una hoja que falla queda en `failed_sheets`.
3. Por regla: `status` `ok`, `with_problems` o `disabled`, y `problems` con código y mensaje en lenguaje del usuario, según la tabla de `automation_rules.py`:
   - `DISABLED_NO_RECIPIENTS`: Smartsheet la apagó porque no encontró a quién avisar.
   - `DISABLED`: apagada por otro motivo o a mano (se muestra el texto de Smartsheet si existe).
   - `NO_RECIPIENTS`: sin correos, sin columnas y sin "todos los compartidos".
   - `RECIPIENT_COLUMN_MISSING`: avisa a una columna que ya no existe.
   - `RECIPIENT_COLUMN_NOT_CONTACT`: avisa a una columna que no es de contacto (por ejemplo, una lista desplegable con nombres): no tiene correos.
   - `RECIPIENT_NOT_SHARED`: avisa a un correo que no tiene la hoja compartida; Smartsheet puede no notificarle.
4. Destinatarios: correos explícitos y columnas (id, título, tipo, si es de contacto).
5. Sólo lectura: reactivar o corregir una regla queda para PEN-07.

## Criterios de aceptación

- CA-01: cada problema de la tabla se detecta con su caso. Prueba: `test_automation_rules.py`.
- CA-02: una regla activa con columna de contacto y destinatarios compartidos es `ok`. Prueba: `test_automation_rules.py::test_healthy_rule`.
- CA-03: la vista de cuenta suma por estado y por problema, filtra `only_problems` y tolera una hoja fallida. Prueba: `test_automations.py::test_account_view`.
- CA-04: sólo lectura. Prueba: `test_automations.py` verifica `writes(...) == []`.
- CA-05: revisión real de la cuenta. Prueba: manual (RESULTADOS).
