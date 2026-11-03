# Base PostgreSQL para el servicio futuro de IDs

- Estado: base `galp_servicios` creada en PostgreSQL de Linux y migración 002 aplicada con respaldo previo, según salida compartida por el usuario el 2026-11-03. Motor de reservas probado en una instancia temporal; sin conexión automática ni instalación en Windows. No habilita escrituras en Smartsheet.
- Alcance: sólo estado operativo de reservas de IDs; Smartsheet conserva los datos de negocio. El panel actual no usa esta base (ADR-B02 y ADR-B18).
- Especificación: `SPEC.md`. El esquema asume IDs generados globalmente únicos y formatos canónicos. Los anchos son mínimos; confirmar el ámbito de proyectos, reglas de años y tratamiento de IDs eliminados antes de operar.
- Motor independiente: `backend/app/services/ids/`; requiere instalar la dependencia opcional `pip install -e '.[ids]'` desde `backend/`. No existe endpoint, proceso automático ni implementación de escritura en Smartsheet.
- La migración `sql/002_auditoria_inicializacion.sql` añade estado de inicialización y auditoría; fue aplicada en `galp_servicios`. No volver a ejecutar 001 ni 002 en esa base. El usuario limitado `galp_ids` está configurado en Linux.
- En Linux `bash servicios/ids/aplicar_migracion_002.sh` crea primero un respaldo privado en `~/galp_backups`, comprueba que su índice sea legible y aplica 002 con sudo. No prueba una restauración completa; hay que ensayarla por separado. Si la migración ya fue aplicada falla sin modificar las tablas existentes.
- `collect_inventory` valida en memoria que el ID visible y el Stable ID coincidan, y rechaza duplicados o formatos incompatibles. El 2026-11-03 se importaron 19 IDs del piloto; una segunda importación idéntica no modificó la auditoría. `IdStore.initialize` acepta además IDs históricos conocidos para elevar máximos, pero no se importaron máximos históricos externos.
- Comando manual desde `backend/`: `.venv/bin/python -m app.services.ids.cli importar` importa las cuatro hojas con workspace comprobado y valida relaciones; una repetición idéntica no cambia la base. Requiere el usuario PostgreSQL `galp_ids` y su archivo privado generado por `crear_usuario_linux.py`.
- `.venv/bin/python -m app.services.ids.cli dry-run` consulta el piloto y PostgreSQL en solo lectura y muestra resultados y estimaciones para filas pendientes, incluso si su fórmula aún está vacía. Reutiliza reservas previas y exige padres confirmados en ambas fuentes; no reserva ni escribe. Las estimaciones no garantizan disponibilidad histórica. Las reservas están deshabilitadas por defecto y no hay proceso automático ni escritura remota.
- El coordinador `connector.py` y la confirmación auditada están probados con adaptador simulado y PostgreSQL temporal. La migración `sql/003_confirmacion.sql` está preparada pero no aplicada en la base real. Falta un adaptador real que garantice escritura condicional atómica y autorización para habilitar escrituras; no conectar un PUT incondicional.
- Transición histórica pendiente: acordar un punto de partida por ámbito usando los máximos verificables y un margen o rango operativo acordado; registrar desde entonces todas las reservas y nunca borrarlas. Sin un histórico completo, el margen reduce riesgo pero no demuestra que un número anterior nunca se haya usado. No activar reservas ni afirmar garantía absoluta antes de acordar la política y resolver la concurrencia de escrituras remotas.

## Preparar Windows Server

1. Identificar la versión de Windows Server y elegir una versión compatible en la [página oficial de instalación](https://www.postgresql.org/download/windows/). Instalar PostgreSQL Server y las herramientas de línea de comandos; pgAdmin es opcional.
2. Durante la instalación definir una contraseña fuerte para el administrador, guardarla en un gestor de secretos y no compartirla por chat ni incorporarla al repositorio. Mantener acceso sólo local si el servicio se ejecutará en el mismo servidor. No publicar el puerto en Internet.
3. Copiar este repositorio al servidor por el medio habitual. Abrir PowerShell en la raíz del repositorio y ejecutar `psql -U postgres -h 127.0.0.1 -d postgres`; introducir la contraseña cuando la solicite. Si `psql` no está en PATH, usar el ejecutable `bin/psql.exe` de la instalación.
4. En la consola `psql`, ejecutar `CREATE DATABASE galp_servicios;` y salir con `\q`. Usar una base nueva y dedicada; si ya existe, detenerse y revisar antes de continuar.
5. Desde PowerShell ejecutar `psql -X -v ON_ERROR_STOP=1 -U postgres -h 127.0.0.1 -d galp_servicios -f servicios/ids/sql/001_esquema.sql`. Solicitará la contraseña. El archivo usa una transacción y falla si las tablas ya existen; no volver a ejecutarlo sobre datos existentes.
6. Verificar con `psql -X -U postgres -h 127.0.0.1 -d galp_servicios -c "\dt"`: deben aparecer `secuencia_id` y `asignacion_id`. No insertar datos reales todavía.

## Antes de usar el servicio

- Definir usuario de aplicación con permisos mínimos, autenticación y almacenamiento seguro de su contraseña. No usar la cuenta administradora desde el servicio.
- Configurar copias de seguridad y ensayar restauración; reconciliar con Smartsheet antes de reanudar asignaciones tras una restauración. Las secuencias y reservas existentes no se borran ni se reinician para volver a numerar.
- Revisar un inventario completo y autorizar su inicialización antes de reservar; una lectura de las cuatro hojas encontró 19 IDs visibles canónicos, pero no prueba el mayor número histórico de filas eliminadas. Sin un registro histórico fiable no se garantiza que los números anteriores a la puesta en marcha nunca se reutilicen.
- El motor reserva en PostgreSQL, pero no confirma escrituras ni se comunica con Smartsheet. La restauración requiere reconciliar y no puede garantizarse mediante una copia antigua solamente.
- Cualquier escritura real requiere autorización expresa y una hoja de prueba acordada; no cambiar `APP_READ_ONLY` por instalar la base.
