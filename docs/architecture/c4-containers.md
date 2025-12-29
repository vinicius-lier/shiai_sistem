# C4 — Nível de Contêineres

```mermaid
flowchart TB
  web[Frontend / Dashboard] --> core[Core API (Django/DRF)\nSchema: core]
  web --> comp[Competition API (Django/DRF)\nSchema: competition]

  core --> dbcore[(PostgreSQL\nschema core)]
  comp --> dbcomp[(PostgreSQL\nschema competition)]

  subgraph "Render PostgreSQL (1 instância)"
    dbcore
    dbcomp
  end
```

Observações:
- Core: identidade (Organization, User, Athlete) e serviços de leitura/validação.
- Competition: eventos/inscrições/pesagem com regras próprias, isoladas do Core.

