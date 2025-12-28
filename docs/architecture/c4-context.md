# C4 — Nível de Contexto (System Context)

```mermaid
flowchart LR
  user[Usuário: Admin/Staff] --> web[Frontend / Dashboard]
  web --> core[Core API]
  web --> comp[Competition API]

  core --> db[(PostgreSQL Render)]
  comp --> db

  subgraph "Banco (mesma instância, schemas isolados)"
    db
  end
```

Notas:
- Uma única instância PostgreSQL com schemas isolados (`core`, `competition`, `ranking` futuro, `public` legado).
- Core e Competition não compartilham modelos; comunicação ocorre por contratos/API e UUIDs.

