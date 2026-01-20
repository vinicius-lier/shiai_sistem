## Regras de Grupo de Faixas

Este documento resume a nova estratégia de `grupo_faixas` que foi persistida e consumida em todas as camadas do sistema operacional SHIAI.

### 1. Definição central

- `Chave.grupo_faixas` é um campo `CharField` com choices (`BRANCA_A_LARANJA`, `VERDE_A_PRETA`, `BRANCA_A_VERDE`, `ROXA_A_PRETA`).
- O grupo é calculado a partir da faixa do atleta e do sexo (`calcular_grupo_faixa` em `atletas/utils.py`).
- Chaves com classe ≥ `SUB-18` (ver `classe_exige_grupo`) exigem grupo — qualquer violação aborta a criação.

### 2. Geração

- `gerar_chave` agrega atletas elegíveis (status aprovado/remanejado, peso_real > 0, categoria_real presente) e determina o grupo coletivo.
- Se atletas com faixas pertencentes a grupos distintos aparecem juntos, a geração aborta para evitar conflitos técnico-sportivos.
- O campo `grupo_faixas` é guardado nos defaults (nova `defaults={'estrutura': {}, 'grupo_faixas': grupo}`) e sincronizado (`save(update_fields=['grupo_faixas'])`) caso a chave já exista.

### 3. Consumo

- `atletas/views.py` passa um `key = (classe_normalizada, sexo, categoria_normalizada, grupo_normalizado)` para todas as comparações.
- O dashboard agora:
  - lista categorias sem chaves usando a tupla canônica;
  - alerta no card “Atletas elegíveis sem chave” quando atletas com peso validado não foram agrupados em nenhuma chave.
- Rankings e resultados utilizam `Chave.grupo_faixas` persistido para garantir que apenas chaves completas são pontuadas.
- A view `detalhe_chave` expõe `chave.get_grupo_faixas_display` ao operador.

### 4. UI e auditoria

- O dashboard mostra o alerta, incluindo nome, classe, peso e `Faixas: ...` do grupo associado ao atleta pendente.
- A tela de detalhe da chave exibe “Faixas: ...” próximo ao título.
- O middleware ignora `/matches/` para que o setor de resultados acesse o módulo de lutas sem falsos 404s.

### 5. Próximos passos

1. Avaliar listas de atletas sem chave (pode virar relatório ou link para `inscrever_atletas`).
2. Vincular alertas ao histórico/ocorrências quando houver remanejamento negado por grupo.
3. Monitorar logs (auditoria) para garantir que o campo `grupo_faixas` não fique vazio em chaves ≥ `SUB-18`.
