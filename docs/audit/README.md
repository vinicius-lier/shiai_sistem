# Auditoria de Integridade (Competition)

Este comando é **somente leitura** e verifica consistência antes de aplicar migrations ou gerar chaves/resultados.

Como rodar:
```bash
cd competition_api
python3 manage.py audit_competition_integrity
```

O que ele checa:
- Duplicatas de `Bracket` pela tupla (event_id, category_code, class_code, sex, belt_group).
- `Registration` confirmadas com snapshot incompleto (class_code, sex, belt_snapshot).
- `Match` órfãos ou com `phase` inválida.
- Formatos `ELIMINATION_WITH_REPECHAGE` sem repescagem/bronze (marca como incompleto por design).

Saída:
- Markdown/texto no stdout com Resumo, Problemas críticos (bloqueiam migrate), Avisos e Próximos passos.

Limites:
- Nenhuma alteração é feita no banco.
- Usa apenas ORM local no schema competition.

