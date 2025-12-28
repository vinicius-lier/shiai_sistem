# Domínio — Invariantes da Competition API

```mermaid
flowchart TB
  EventStatus["Event.status\nDRAFT → OPEN → CLOSED"]
  RegStatus["Registration.status\nPENDING → WEIGHED → APPROVED\n(any) → BLOCKED"]
  inv1["Inv: não criar Registration se Event != OPEN"]
  inv2["Inv: não criar Weighing se Reg != PENDING"]
  inv3["Inv: bloquear pesagem/alteração se Reg == BLOCKED"]
  inv4["Inv: chaves só quando Event == CLOSED (fora do escopo)"]

  EventStatus --> inv1
  RegStatus --> inv2
  RegStatus --> inv3
  EventStatus --> inv4
```

Resumo das regras:
- Criação de inscrição exige `Event.status == OPEN`.
- Pesagem exige `Registration.status == PENDING` e não pode ocorrer se `status == BLOCKED`.
- Aprovação exige pesagem prévia (`status == WEIGHED`).
- Geração de chaves depende de evento `CLOSED` (fora do escopo atual).

