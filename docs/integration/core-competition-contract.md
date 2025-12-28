# Integração Core ↔ Competition — Contrato Mínimo (read-only)

Princípio: Competition não lê o schema `core` diretamente. Toda verificação é via API do Core, usando UUIDs. Comunicação segura com headers de correlação.

## Endpoints do Core (expostos ao Competition)

### 1) Resolver organização por slug
`GET /api/core/organizations/{slug}`

Resposta 200:
```json
{
  "id": "uuid-org",
  "name": "Organização X",
  "slug": "organizacao-x",
  "is_active": true
}
```

Erros:
- 404 se não existir ou inativa.

### 2) Validar atleta pertence à organização
`GET /api/core/organizations/{org_id}/athletes/{athlete_id}`

Resposta 200:
```json
{
  "id": "uuid-athlete",
  "name": "Atleta Y",
  "birth_date": "2005-01-15",
  "sex": "M",
  "belt": "AZUL",
  "is_active": true
}
```

Erros:
- 404 se não pertencer, não existir ou estiver inativo.
- 403 apenas se houver política de acesso adicional (opcional).

## Headers recomendados (todas as chamadas)
- `X-Request-ID`: correlação ponta-a-ponta.
- `X-Organization-ID`: organização em nome da qual a operação ocorre.

## Observações
- Competition só confia em UUIDs após validação no Core.
- Sem retries cegos; falha rápida se Core responder erro.

