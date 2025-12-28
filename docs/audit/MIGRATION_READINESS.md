# Migration Readiness (Competition)

[ ] Nenhuma duplicata de Bracket na tupla (event_id, category_code, class_code, sex, belt_group).  
[ ] Zero Registration confirmada com snapshot incompleto (class_code, sex, belt_snapshot).  
[ ] Nenhum Match órfão; `phase` válida (MAIN/REPECHAGE/BRONZE/FINAL).  
[ ] Nenhuma referência a grupo 9 (somente grupos 1..8, com regras de sexo nos grupos 7/8).  
[ ] Todas as migrations pendentes listadas (registrations 0003; brackets 0002/0003; matches 0003).  
[ ] Documentação sem conflito (README_ARCHITECTURE.md, DOMAIN_MODEL.md, docs/architecture, docs/domain, docs/integration, docs/audit).  
[ ] Formatos automáticos conferidos (1=WO, 2=BEST_OF_3, 3–5=RR, ≥6=ELIMINATION_WITH_REPECHAGE).  
[ ] Pontos de luta (IPPON 10, WAZA-ARI 7, YUKO 5, HANSOKUMAKE 3, WO 1) usados apenas para desempate interno.  
[ ] Vencedor sempre manual; Ranking só lê OfficialResult (Competition→Ranking read-only).  
[ ] Event fechado antes de gerar chaves/resultados oficiais.  

