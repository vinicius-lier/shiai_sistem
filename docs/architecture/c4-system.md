# C4 — Sistema (Contexto e Contêineres)

## Nível 1 — Contexto (atual, sem integração ativa)
```mermaid
flowchart LR
  user[Usuário (Admin/Staff)] --> web[Frontend / Dashboard]
  web --> core[Core API]
  web --> comp[Competition API]

  core --> db[(PostgreSQL Render)]
  comp --> db

  subgraph "Instância única • Schemas isolados"
    db
  end
```

Notas:
- Schemas isolados: `core` (Core API), `competition` (Competition API), `ranking` futuro, `public` legado.
- Core e Competition não acessam tabelas uma da outra.

## Nível 2 — Contêineres (conceitual)
```mermaid
flowchart TB
  web[Frontend / Dashboard] --> core[Core API (Django)\nSchema: core]
  web --> comp[Competition API (Django)\nSchema: competition]

  core --> dbcore[(PostgreSQL\nschema core)]
  comp --> dbcomp[(PostgreSQL\nschema competition)]

  subgraph "PostgreSQL (Render, 1 instância)"
    dbcore
    dbcomp
  end

  %% Integração futura (planejada)
  core -. HTTP (planned) .-> comp
  comp -. HTTP (planned) .-> core
```

Diretrizes:
- Integração Core ↔ Competition será via HTTP/contratos; não há integração ativa hoje.
- Sem ForeignKey cruzada; apenas UUID e contratos quando necessário.

