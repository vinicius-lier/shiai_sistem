# Visão Geral — Shiai System

## 1. Panorama
- Sistema modular, multi-API: Core API (identidade) e Competition API (eventos/inscrição/pesagem).
- Banco único PostgreSQL no Render, com schemas isolados (`core`, `competition`, `ranking` futuro, `public` legado intocado).
- Sem ForeignKey entre APIs; comunicação futura apenas por UUID e contratos explícitos.
- Regras de negócio vivem em `services.py`; views/admin não carregam lógica.

## 2. Por que multi-API
- Isolamento de domínios e evolução independente.
- Possibilidade de separar infra/bancos no futuro sem refatoração profunda.
- Minimizar acoplamento: cada API é dona de seu schema e das suas entidades.

## 3. Papel de cada API
- Core API (schema `core`):
  - Dono de Organization, User (role-based), Athlete.
  - Garante identidade, pertencimento e leitura segura via services.
  - Não cria/gerencia eventos, inscrições ou pesagens.
- Competition API (schema `competition`):
  - Dono de Event, Registration, Weighing.
  - Controla fluxo de evento (DRAFT→OPEN→CLOSED) e inscrição/pesagem (PENDING→WEIGHED→APPROVED / BLOCKED).
  - Não altera dados do Core; consome apenas UUIDs validados por contrato.

## 4. Invariantes de Domínio
- Core:
  - Atleta é imutável dentro do Core (identidade, não participação).
  - Faixa pertence ao atleta (enum controlado).
  - Organização define o tenant; toda identidade pertence a uma Organization.
- Competition:
  - Event só aceita inscrição se `status == OPEN`.
  - Registration só registra pesagem se `status == PENDING`.
  - `BLOCKED` é estado terminal de Registration.
  - Nenhuma regra vive fora dos services; services são a única porta de regras.

## 5. Camada de services como fonte de verdade
- Toda regra de negócio está em `services.py` de cada app.
- Fail fast: estados inválidos geram erro imediato.
- Integração futura Core ↔ Competition será via contratos; nunca via acesso direto ao schema alheio.

