# C4 — Componentes (Competition)

```mermaid
flowchart TB
  subgraph comp["Competition API (schema competition)"]
    ev[events\nEvent (organization_id UUID)]
    reg[registrations\nRegistration (event_id, athlete_id, organization_id UUID)]
    wei[weighings\nWeighing (registration_id UUID)]
    evsvc[events/services.py]
    regsvc[registrations/services.py]
    weisvc[weighings/services.py]
  end

  evsvc --> ev
  regsvc --> reg
  weisvc --> wei
```

Princípios:
- Nenhuma FK para o Core; apenas UUIDs.
- Estados controlados por enums `EventStatus` e `RegistrationStatus`.

