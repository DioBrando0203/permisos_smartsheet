# Diagramas de la KMV 2.0 (MP-D1 a MP-D5)

Estado 2026-11-23. Los diagramas están en Mermaid: GitHub y VS Code (con la vista previa de Markdown) los dibujan solos. El texto que los explica está en `HOJAS_Y_PIEZAS.md` y `SERVICIO_Y_FLUJO.md`.

## MP-D1: hojas y quién llena qué

La maestra es la única hoja donde se crean filas. Las hojas de equipo las llena el servicio y le devuelven los resultados. Las listas de apoyo alimentan fórmulas de la maestra.

```mermaid
flowchart TB
    subgraph LISTAS["Listas de apoyo (carpeta List de la 2.0)"]
        CUS["Customer List"]
        PSL["Project Status List"]
        CON["Contact List"]
    end

    M["PROJECT KMV 2.0<br/>maestra: proyectos y trámites<br/>79 columnas, todas las compañías"]

    subgraph EQUIPOS["Hojas de equipo (las llena el servicio)"]
        PER["Permits"]
        MOT["MOT #amp; Packages"]
        REC["Records Requests"]
        BIL["Billing"]
        DTK["Design Tickets"]
    end

    CUS -- "fórmula: Client Access" --> M
    PSL -- "fórmula: Phase y Closed" --> M
    REC -- "fórmula: Records Status" --> M
    M -- "servicio: crea la fila y copia el proyecto" --> PER & MOT & REC & BIL & DTK
    PER & MOT & BIL & DTK -- "servicio: estado y resultados" --> M
    CON -- "servicio: a quién avisar el metraje" --> BIL
```

## MP-D2: vistas, quién las usa y de dónde leen

Nadie trabaja en las hojas: cada persona entra por su vista y ve sólo lo suyo.

```mermaid
flowchart LR
    CO["Coordinadora"] --> VPR["PROJECTS<br/>crea proyectos"]
    CO --> VPE["PERMITS<br/>crea trámites"]
    DI["Diseño"] --> VDE["DESIGN<br/>por Designers<br/>ve Records, Design Ticket y Mile Post"]
    PT["Equipo de permisos"] --> VPT["PERMITS TEAM<br/>por Permitting Team"]
    MP["Persona de MOT y paquetes"] --> VMO["MOT #amp; PACKAGES<br/>todo"]
    RE["Records"] --> VRE["RECORDS<br/>por Records Owner"]
    FA["Facturación"] --> VBI["BILLING<br/>todo"]
    DT["DT Owner"] --> VDT["DESIGN TICKETS<br/>por DT Owner"]
    CL["Cliente"] --> VCU["CUSTOMERS<br/>por Client Access, sólo lectura"]

    VPR --> M[("Maestra")]
    VPE --> M
    VCU --> M
    VDE --> RDP["Reporte Design Projects"] --> M
    VPT --> PER[("Permits")]
    VMO --> MOT[("MOT #amp; Packages")]
    VRE --> REC[("Records Requests")]
    VBI --> BIL[("Billing")]
    VDT --> DTK[("Design Tickets")]
```

## MP-D3: el flujo de un proyecto

Quién hace cada paso: una persona, el servicio o Smartsheet solo (automatizaciones y fórmulas).

```mermaid
sequenceDiagram
    actor C as Coordinadora
    participant M as Maestra
    participant S as Servicio
    participant H as Hoja del equipo
    participant A as Automatizaciones
    actor E as Equipo
    actor I as Ingeniero

    C->>M: crea el proyecto (vista PROJECTS)
    S->>M: pone el ID (en menos de un minuto)
    A-->>E: aviso a diseño con el enlace a su vista
    E->>M: diseña y pasa a Design Needs QC
    A-->>I: QC pendiente, y otro aviso si pasa más de 1 día
    C->>M: crea los trámites con Parent Project y Agency (vista PERMITS)
    S->>M: pone cada trámite bajo su proyecto y le da el ID
    S->>H: crea la fila del trámite y copia el proyecto
    A-->>E: aviso de asignación con el enlace a su vista
    E->>H: trabaja el trámite (estados, fechas, números)
    S->>M: devuelve estado y resultados
    E->>H: facturación corrige el metraje en Billing
    S->>M: lleva el metraje a la maestra
    S-->>E: aviso de metraje al diseñador, a la persona de avisos y al ingeniero
    C->>M: cierra o cancela (CANCELLED, nunca se borra)
```

## MP-D4: cómo corre el servicio

```mermaid
flowchart TD
    A["Mira la versión de la maestra<br/>cada 5 s; cada 30 s tras 2 min sin cambios"] --> B{"¿Cambió algo o<br/>pasaron 60 s?"}
    B -- "no" --> A
    B -- "sí" --> C["ID Manager:<br/>numera, pone cada trámite bajo su proyecto, hereda el ID"]
    C --> D["Pasos en orden: herencia, Records, Billing, metraje,<br/>Permits, MOT y paquetes, Design Tickets, listas, Obs"]
    D --> E{"Por cada paso:<br/>¿cambiaron sus hojas o toca forzar?"}
    E -- "no" --> F["Se salta y repite su último resultado"]
    E -- "sí" --> G["Lee y escribe en Smartsheet<br/>(un pedido por hoja; freno en 250 por minuto)"]
    F --> H["Registro y estado:<br/>/api/ids/logs y /api/ids/status"]
    G --> H
    H --> A
```

## MP-D5: qué depende del servicio

```mermaid
flowchart LR
    subgraph SOLO["Smartsheet solo: funciona aunque el servicio esté apagado"]
        V1["Vistas y lo que cada persona escribe"]
        V2["Fórmulas: ID visible, días, fase,<br/>cerrado, Client Access, Records Status"]
        V3["Colores (formato condicional)"]
        V4["Automatizaciones de aviso"]
    end
    subgraph SERVICIO["Necesita el servicio: se atrasa si está apagado y se pone al día al volver"]
        S1["ID de cada proyecto (Pending ID mientras tanto)"]
        S2["Trámites bajo su proyecto"]
        S3["Filas y datos en las hojas de equipo"]
        S4["Estados y resultados de vuelta a la maestra"]
        S5["Obs, listas de Parent Project y Linked Tracking"]
        S6["Metraje corregido por facturación y su aviso"]
    end
    S3 -. "las filas nuevas disparan los avisos de asignación" .-> V4
```
