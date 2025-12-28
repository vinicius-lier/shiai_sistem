# Especificação — audit_competition_integrity (read-only)

Objetivo: verificar integridade do domínio Competition antes de migrar/gerar chaves, sem modificar dados.

Escopo (ORM somente leitura, schema competition):
- Brackets duplicados pela tupla (event_id, category_code, class_code, sex, belt_group).
- Registrations confirmadas com snapshot incompleto (class_code, sex, belt_snapshot nulos).
- Matches órfãos (sem bracket) ou com phase inválida (fora de MAIN/REPECHAGE/BRONZE/FINAL, se o campo existir).
- Brackets no formato ELIMINATION_WITH_REPECHAGE sem repescagem/bronze (heurística: ausência de phase REPECHAGE ou <2 matches BRONZE).

Regras:
- Nenhuma escrita/alteração; apenas SELECT com ORM da Competition.
- Sem endpoints; comando management.
- Exceções claras; nada de try/except genérico encobrindo erros.

Saída (stdout em texto/markdown):
- Resumo (contagens)
- Problemas críticos (bloqueiam migrate)
- Avisos (não bloqueiam)
- Próximos passos sugeridos

Pontos de verificação:
1) Brackets duplicados:
   - Group by (event_id, category_code, class_code, sex, belt_group); listar tuplas com count>1 e IDs.
2) Registrations:
   - `is_confirmed=True` AND (class_code IS NULL OR sex IS NULL OR belt_snapshot IS NULL).
3) Matches:
   - `bracket_id` nulo ou bracket inexistente.
   - `phase` não em {MAIN, REPECHAGE, BRONZE, FINAL} (se o campo estiver presente).
4) Repescagem:
   - Brackets ELIMINATION_WITH_REPECHAGE sem phase REPECHAGE ou sem ao menos 2 BRONZE; classificar como “incompleto” (aviso).

Uso previsto:
```bash
python3 manage.py audit_competition_integrity
```

Limites:
- Não toca Core ou Ranking.
- Não resolve dados, só reporta.
- Se algum campo/modelo não existir na versão atual, relatar “não aplicável” e seguir.

