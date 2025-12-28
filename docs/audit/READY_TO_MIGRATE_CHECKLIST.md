# Checklist — Pronto para Migrate (Competition)

- [ ] Migrations pendentes identificadas (não rodar automaticamente):
  - `registrations` (snapshot class_code/sex/belt_snapshot) — 0003…
  - `brackets` (class/sex/belt_group + índices) — 0002, 0003
  - `matches` (phase/source refs) — 0003
- [ ] Nenhuma duplicata de `Bracket` para a tupla `(event_id, category_code, class_code, sex, belt_group)`.
- [ ] `Registration` com `is_confirmed=True` não possui snapshot faltante (`class_code`, `sex`, `belt_snapshot`).
- [ ] `Match` sem órfãos: `bracket_id` válido; `phase` ∈ {MAIN, REPECHAGE, BRONZE, FINAL}.
- [ ] Brackets `ELIMINATION_WITH_REPECHAGE` têm repescagem/bronzes criados; se ainda não implementado, documentado como “incompleto por design”.
- [ ] Event `CLOSED` antes de gerar chaves/resultados oficiais.
- [ ] WinMethod inclui YUKO (pontos de luta: IPPON 10, WAZA-ARI 7, YUKO 5, HANSOKUMAKE 3, WO 1) – usado só para desempate interno.
- [ ] Documentação canônica revisada (README_ARCHITECTURE.md, DOMAIN_MODEL.md, docs/architecture, docs/domain, docs/integration).

Comandos recomendados (quando for aplicar):
```bash
python3 manage.py showmigrations registrations brackets matches
python3 manage.py audit_competition_integrity
# aplicar somente quando o checklist estiver verde:
python3 manage.py migrate registrations brackets matches --skip-checks
```

