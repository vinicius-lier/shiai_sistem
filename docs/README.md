# Shiai System — Documentação de Arquitetura e Domínio

Este diretório consolida a visão arquitetural e as regras de domínio do Shiai System, cobrindo Core (identidade) e Competition (eventos/inscrições/pesagem).  
Os diagramas usam Mermaid; a navegação está organizada por arquitetura, domínio e integração.

## Estrutura
- `architecture/` — Diagramas C4 (contexto, contêineres, componentes).
- `domain/` — Bounded contexts e invariantes de negócio.
- `integration/` — Contrato Core ↔ Competition e fluxo controlado.

## Princípios
- Domínios isolados por schema PostgreSQL (`core`, `competition`, `ranking` futuro).
- Regras de negócio vivem em `services.py`, não em views, admin ou signals.
- Comunicação entre domínios via UUID e contratos explícitos (sem FK cruzada).

