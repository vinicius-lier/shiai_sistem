# Shiai System — Domínio (texto)

## Core Domain
- Entidades: Organization, User, Athlete.
- Regras:
  - Athlete é imutável em relação à competição (identidade, não participação).
  - User pertence a uma Organization; controle de acesso por `role` (ADMIN/STAFF).
  - Faixa (belt) pertence ao atleta e é controlada via enum.
- Não pertence ao Core: eventos, inscrições, pesagens, chaves, ranking, relatórios de competição.

## Competition Domain
- Entidades: Event, Registration, Weighing.
- Regras invariantes:
  - Event precisa estar `OPEN` para aceitar Registration.
  - Registration segue ciclo: PENDING → WEIGHED → APPROVED (ou BLOCKED como terminal).
  - Weighing só ocorre quando Registration está `PENDING`; `BLOCKED` impede pesagem/alteração.
- Não pertence à Competition: criação/alteração de Athlete/User/Organization; regras de ranking; chaves (ainda não); dados sensíveis do Core.
- Chaveamento (estado atual):
  - Pré-condições: evento `CLOSED`; inscrição elegível (is_confirmed, status ∈ {WEIGHED, APPROVED}, não desclassificada, não BLOCKED, categoria final, snapshot classe/sexo/faixa).
  - Filtros/agrupamento: classe (aliases: AULAO/FESTIVAL/CHUPETINHA → AULAO; ADULTO → SÊNIOR; MASTER → VETERANO), sexo, categoria, grupo de faixas (resolve_belt_group).
  - Quantidade → formato: 1=WO; 2=BEST_OF_3; 3–5=ROUND_ROBIN; ≥6=ELIMINATION_WITH_REPECHAGE (repescagem estruturada, dois bronzes).
  - Pontos de luta: IPPON 10, WAZA-ARI 7, YUKO 5, HANSOKUMAKE 3, WO 1 (somente desempate interno; vencedor manual).

## Limites e o que cruza fronteira
- Dados que cruzam: UUIDs (`organization_id`, `athlete_id`, `event_id`, `registration_id`) validados por contrato.
- Dados que não cruzam: modelos/ORM, FKs, joins entre schemas, credenciais ou campos sensíveis do Core.
- Integração futura (services → adapters) fará validação antes de mutar estado na Competition.

## Responsabilidades futuras (não implementadas)
- Geração de chaves.
- Ranking e pontuação.
- Relatórios de competição.
- Gateway/API pública unificada.

## Future Integration: Core ↔ Competition (conceitual)
- Competition consome dados do Core apenas para validação (organization_id, athlete_id), nunca para mutar.
- Formas possíveis: leitura via API HTTP, cache/snapshot de existência, gateway.
- Regras:
  - Competition nunca altera Core.
  - UUIDs são a única ponte; sem FK cruzada.
  - Falha do Core não deve derrubar Competition (fail fast, tratar erro).

