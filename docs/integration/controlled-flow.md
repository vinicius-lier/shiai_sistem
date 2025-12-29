# Fluxo Controlado Core ↔ Competition

```mermaid
flowchart LR
  FE[Frontend] -->|slug org| CoreOrg[Core: GET /organizations/{slug}]
  CoreOrg -->|org_id| FE
  FE -->|event_id, athlete_id, organization_id| CompReg[Competition: register_athlete]
  CompReg -->|validação| CoreAth[Core: GET /organizations/{org_id}/athletes/{athlete_id}]
  CoreAth -->|ok| CompReg
```

Passo a passo:
1) Frontend resolve organização no Core (slug → org_id).
2) Para registrar inscrição, Competition recebe `event_id`, `athlete_id`, `organization_id`.
3) Competition chama Core para confirmar que o atleta pertence à organização e está ativo.
4) Só então executa `register_athlete(...)`.

Headers recomendados:
- `X-Request-ID` — correlação ponta-a-ponta.
- `X-Organization-ID` — contexto da organização.

Timeouts:
- Curtos (2–3s) para evitar travas; em erro, falhar explicitamente (sem retry cego).

Observação:
- Competition não consulta diretamente o schema `core`; todo consumo é via API do Core.

