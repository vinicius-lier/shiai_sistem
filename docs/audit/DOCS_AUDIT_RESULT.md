# DOCS Audit Result (consolidado)

## Fontes canônicas
- README_ARCHITECTURE.md
- DOMAIN_MODEL.md
- docs/architecture/*
- docs/domain/*
- docs/integration/*
- docs/audit/* (mapa/checklist/audit spec)

## Duplicados / Ambíguos
- AUDITORIA_*.md, RELATORIO_* (conteúdo de auditoria legado, possível sobreposição com docs/ atuais)
- GUIA_*, MANUAL_*, ESPECIFICACAO_* (materiais operacionais que podem repetir regras; revisar e alinhar)
- docs/auditorias/* (auditorias antigas; consolidar no novo docs/audit)

## Obsoletos (marcar com aviso)
- Qualquer doc que cite campos legados (classe_escolhida, categoria_escolhida, status_inscricao antigo) ou fluxo pré-normalizado.

## Ação sugerida
- Manter canônicos atualizados.
- Nos duplicados/ambíguos: adicionar aviso no topo “⚠️ Documento histórico / não canônico. Consulte <doc canônico>”.
- Nos obsoletos: marcar como histórico; não usar para decisão de produto.

