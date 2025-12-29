# Shiai System — Arquitetura (C4 textual)

## C4 — Context Diagram (texto)
- Sistemas:
  - Core API: identidade (Organization, User, Athlete) e serviços de validação.
  - Competition API: eventos, inscrições, pesagens, estados esportivos.
- Atores: Admin, Staff.
- Relação: Core e Competition compartilham a mesma instância PostgreSQL, mas operam em schemas isolados (`core`, `competition`). Não há ForeignKey cruzada; a referência entre domínios é apenas por UUID e por contrato (a ser definido).

## C4 — Container Diagram (texto)
- Core API: Django; persiste no schema `core` do PostgreSQL.
- Competition API: Django; persiste no schema `competition` do PostgreSQL.
- Banco: uma instância PostgreSQL com schemas isolados (`core`, `competition`, `ranking` futuro, `public` legado).
- Não existe dependência direta entre containers; integração futura será via HTTP/contrato, não por acesso direto a tabelas.

## C4 — Component Diagram (alto nível, texto)
- Core API:
  - `organizations` (Organization)
  - `accounts` (User, roles)
  - `athletes` (Athlete, faixa)
  - `services` (validação de pertencimento, leitura segura, controle por role)
- Competition API:
  - `events` (Event, status DRAFT/OPEN/CLOSED)
  - `registrations` (Registration, status PENDING/WEIGHED/APPROVED/BLOCKED)
  - `weighings` (Weighing)
  - `services` (regras de fluxo e invariantes)
- Observação: nenhuma FK entre APIs; apenas UUIDs e regras explícitas nos services.

## Regras de fronteira (Core ↔ Competition)
- ❌ Competition nunca escreve no Core.
- ❌ Competition nunca assume existência sem validar.
- ✅ Core é fonte de verdade para Organization/Athlete.
- ✅ Competition falha cedo se Core negar ou não responder.
- ✅ Adapters de leitura são substituíveis (SQL hoje, HTTP/Gateway amanhã).

### Teste mental: se o Core cair agora
- Novos registros na Competition falham (validação não passa).
- Eventos/inscrições já existentes continuam persistidos.
- Sem corrupção de banco; nenhuma escrita no schema core ocorre.

## Formação de Chaves — Lógica Atual
- Pré-condições: evento `CLOSED`; inscrição elegível (is_confirmed, status ∈ {WEIGHED, APPROVED}, não disqualified, não BLOCKED, category_code_final, snapshot de classe/sexo/faixa).
- Filtros/agrupamento: classe (aliases: AULAO/FESTIVAL/CHUPETINHA → AULAO; ADULTO → SÊNIOR; MASTER → VETERANO), sexo, categoria, grupo de faixas (resolve_belt_group), por evento.
- Regra por quantidade → formato:
  - 1 atleta: WO, sem matches.
  - 2 atletas: BEST_OF_3 (3 lutas).
  - 3–5 atletas: ROUND_ROBIN (desempate: vitórias, pontos de luta, confronto direto).
  - ≥6 atletas: ELIMINATION_WITH_REPECHAGE (repescagem estruturada; duas repescagens e dois bronzes; vencedor sempre manual).
- Pontos de luta (interno): IPPON 10, WAZA-ARI 7, YUKO 5, HANSOKUMAKE 3, WO 1; apenas desempate interno; vencedor sempre manual; Ranking nunca lê matches diretamente.
- Aliases de classe: AULAO=FESTIVAL=CHUPETINHA; ADULTO=SÊNIOR; MASTER=VETERANO.
- Grupos de faixas (sexo-sensível nos grupos 7/8) conforme tabela do domínio; grupo 9 removido.
## Escrita é proibida na Competition
- Qualquer criação/atualização de Organization ou Athlete deve ocorrer apenas na Core API.
- Competition só lê e valida via adapters (`CoreReadContract` + implementação atual `CoreSQLReader`); não há código de escrita apontando para o schema `core`.
- Qualquer tentativa futura de escrita deve ser rejeitada e movida para o domínio Core.

## Validação / teste de integridade (conceitual)
- Teste de integração deve confirmar que:
  - Chamadas de Competition ao Core são apenas SELECT (nenhuma operação de escrita).
  - Se o Core estiver indisponível, a Competition falha cedo nas validações sem corromper dados locais.
  - Nenhum join/ORM cruzado é usado (somente UUID + adapter).

