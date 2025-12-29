# Mapa de Documentos (auditoria)

| caminho | categoria | motivo curto | ação sugerida |
| --- | --- | --- | --- |
| README_ARCHITECTURE.md | FONTE DA VERDADE | Arquitetura geral, fronteiras, formatos de chave | Manter e manter atualizado |
| DOMAIN_MODEL.md | FONTE DA VERDADE | Domínio Core/Competition/Ranking consolidado | Manter e manter atualizado |
| docs/architecture/* | FONTE DA VERDADE | C4 e visão estrutural | Manter |
| docs/domain/* | FONTE DA VERDADE | Regras de domínio e invariantes | Manter |
| docs/integration/* | FONTE DA VERDADE | Contratos Core ↔ Competition ↔ Ranking | Manter |
| docs/audit/* | NOVO | Auditoria e checklist de migração | Manter como referência de saneamento |
| AUDITORIA_*.md / RELATORIO_* / RESUMO_* | DUPLICADO/AMBÍGUO | Podem repetir regras antigas ou parciais | Consolidar conteúdo em docs/ ou marcar como histórico |
| GUIA_* / MANUAL_* / ESPECIFICACAO_* | AMBÍGUO | Instruções operacionais pontuais; verificar versão | Revisar e, se coerente, referenciar como material de apoio |
| docs/exemplos/*.csv | APOIO | Exemplos de importação/listagem | Manter como exemplos; não fonte de regra |
| arquivos que citam classe_escolhida/categoria_escolhida/status_inscricao | OBSOLETO | Referenciam campos legados | Marcar como histórico ou remover após confirmação |

Critério: não apagar nada automaticamente; usar estas tags para consolidar um conjunto canônico (README_ARCHITECTURE.md, DOMAIN_MODEL.md, docs/architecture, docs/domain, docs/integration).

