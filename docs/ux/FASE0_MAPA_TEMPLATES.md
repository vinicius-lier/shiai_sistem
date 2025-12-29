### FASE 0 — Auditoria e Mapa de Templates (NÃO CODAR)

**Projeto:** SHIAI (Django Templates)  
**Escopo desta fase:** inventário + classificação + dependências visuais + identificação de telas críticas/duplicadas/sensíveis.  
**Importante:** nenhuma alteração de backend/URLs/regras; este arquivo é apenas documentação.

---

## 1) Inventário (contagem)

- **Total de templates `.html` encontrados:** 122
  - **App `atletas` (legacy + multi-tenant):** 105
  - **Projeto `competition_api`:** 17
  - **`ranking_api`:** 0 templates HTML (neste repositório)

---

## 2) Bases e dependências visuais (foto atual)

### 2.1 Bases principais (pontos de acoplamento)

- **`atletas/templates/atletas/base.html`**
  - **Bootstrap:** Sim (CSS/JS via CDN)
  - **CSS inline:** Sim (muito)
  - **JS inline:** Sim
  - **Observação:** base “global” usada por operacional + wrappers `layouts/base_*`.

- **`atletas/templates/atletas/academia/base_academia.html`**
  - **Bootstrap:** Sim (CSS via CDN)
  - **CSS inline:** Sim (muito; redefine `.container`, `.btn`, `.card`, etc.)
  - **JS inline:** Sim
  - **Observação:** base separada para o portal Academia, com visual próprio.

- **`competition_api/matches/templates/matches/base_competition.html`**
  - **Bootstrap:** Sim (CSS/JS via CDN)
  - **Tokens próprios:** Sim (`matches/ui/_tokens.html` + `_ui_styles.html`)
  - **CSS inline:** Sim (alguns blocos)
  - **JS inline:** Não (base só carrega bootstrap.bundle)

- **`competition_api/matches/templates/matches/base_kiosk.html`**
  - **Bootstrap:** Sim
  - **Tokens próprios:** Sim
  - **CSS inline:** Sim
  - **JS inline:** Não (base só carrega bootstrap.bundle)

### 2.2 “Tokens” existentes hoje

- **`atletas/templates/atletas/ui/_tokens.html`**
  - Arquivo de tokens/utilitários (CSS puro) — hoje **não é garantido** que esteja ativo em todas as páginas (depende de como a base inclui/ativa).

- **`competition_api/matches/templates/matches/ui/_tokens.html`**
  - Tokens ativos em `competition_api` (body `data-shiai-ui="1"`).

---

## 3) Telas críticas, duplicadas e sensíveis (risco operacional)

### 3.1 Telas críticas de fluxo (não podem quebrar)

- **AUTH**
  - `atletas/templates/atletas/landing.html` (porta de entrada; contém ações de login)
  - `atletas/templates/atletas/academia/selecionar_login.html` (seleção Operacional x Academia)
  - `atletas/templates/atletas/login_operacional.html`
  - `atletas/templates/atletas/academia/login.html`
  - `atletas/templates/atletas/selecionar_organizacao.html` (superuser)
  - `atletas/templates/atletas/alterar_senha_obrigatorio.html`

- **PESAGEM (evento ao vivo)**
  - `atletas/templates/atletas/pesagem.html`
  - `atletas/templates/atletas/pesagem_mobile.html`
  - Modais: `atletas/templates/atletas/partials/modal_pesagem.html` e `atletas/templates/atletas/includes/pesagem_modal.html`

- **MESA / RESULTADO (evento ao vivo)**
  - `competition_api/matches/templates/matches/mesa.html` (registrar resultado)
  - `atletas/templates/atletas/luta_mobile.html` (registro mobile — standalone)

- **TELÃO**
  - `competition_api/matches/templates/matches/acompanhamento.html` (TV)

### 3.2 Telas duplicadas (operacional vs academia)

- **Cadastro/listagem de atletas**
  - Operacional: `atletas/templates/atletas/cadastrar_atleta.html`, `atletas/templates/atletas/lista_atletas.html`
  - Academia: `atletas/templates/atletas/academia/cadastrar_atleta.html`, `atletas/templates/atletas/academia/lista_atletas.html`

- **Inscrição**
  - Operacional: `atletas/templates/atletas/inscrever_atletas.html`
  - Academia: `atletas/templates/atletas/academia/inscrever_atletas.html`

- **Chaves**
  - Operacional: `atletas/templates/atletas/detalhe_chave.html`, `atletas/templates/atletas/lista_chaves.html`
  - Academia: `atletas/templates/atletas/academia/ver_chaves.html`, `atletas/templates/atletas/academia/detalhe_chave.html`

### 3.3 Telas sensíveis a erro humano (precisam UX “à prova de ginásio”)

- **Pesagem:** `pesagem.html`, `pesagem_mobile.html` (+ modais)
- **Mesa/resultado:** `competition_api/matches/mesa.html`, `atletas/luta_mobile.html`
- **Geração/edição de chaves:** `gerar_chave.html`, `gerar_chave_manual.html`, `detalhe_chave.html`
- **Admin financeiro/pagamentos:** `administracao/conferencia_pagamentos_*`, `administracao/despesas.html`, `administracao/validar_pagamento.html`

---

## 4) Lista completa de templates (com classificação)

Legenda de dependências visuais (heurística conservadora):
- **Bootstrap**: Sim se **herda** de `atletas/base.html`, `atletas/academia/base_academia.html` ou bases do `competition_api`.
- **CSS inline**: Sim se contém `<style>`.
- **JS inline**: Sim se contém `<script>`.
- **Tokens**: Sim quando inclui `_tokens.html` do respectivo projeto ou é arquivo de tokens.

### 4.1 App `atletas` (105 templates)

| Caminho | Papel | Tipo | Bootstrap | CSS inline | JS inline | Tokens |
|---|---|---:|:---:|:---:|:---:|:---:|
| `atletas/templates/atletas/base.html` | OPERACIONAL | base | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/academia/base_academia.html` | ACADEMIA | base | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/administracao/base_admin.html` | OPERACIONAL | base | Sim | Não | Não | Não |
| `atletas/templates/atletas/layouts/base_auth.html` | AUTH | base | Sim | Sim | Não | Não |
| `atletas/templates/atletas/layouts/base_public.html` | INSTITUCIONAL | base | Sim | Sim | Não | Não |
| `atletas/templates/atletas/layouts/base_operational.html` | OPERACIONAL | base | Sim | Não | Não | Não |
| `atletas/templates/atletas/layouts/base_academy.html` | ACADEMIA | base | Sim | Não | Não | Não |
| `atletas/templates/atletas/layouts/base_weighing.html` | PESAGEM | base | Sim | Não | Não | Não |
| `atletas/templates/atletas/layouts/base_table.html` | MESA | base | Sim | Não | Não | Não |
| `atletas/templates/atletas/ui/_tokens.html` | (infra) | component | Não | Sim | Não | Sim |
| `atletas/templates/atletas/ui/_alerts.html` | (infra) | component | Sim | Sim | Não | Não |
| `atletas/templates/atletas/ui/_buttons.html` | (infra) | component | Sim | Sim | Não | Não |
| `atletas/templates/atletas/ui/_status_badge.html` | (infra) | component | Sim | Sim | Não | Não |
| `atletas/templates/atletas/ui/_page_head.html` | (infra) | component | Sim | Não | Não | Não |
| `atletas/templates/atletas/ui/_table.html` | (infra) | component | Sim | Sim | Não | Não |
| `atletas/templates/atletas/includes/pesagem_modal.html` | PESAGEM | modal | Sim | Não | Não | Não |
| `atletas/templates/atletas/partials/modal_pesagem.html` | PESAGEM | modal | Sim | Não | Não | Não |
| `atletas/templates/atletas/landing.html` | INSTITUCIONAL | page | Sim | Sim | Não | Não |
| `atletas/templates/atletas/login_operacional.html` | AUTH | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/academia/login.html` | AUTH | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/academia/selecionar_login.html` | AUTH | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/selecionar_organizacao.html` | AUTH | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/alterar_senha_obrigatorio.html` | AUTH | page | Sim | Não | Sim | Não |
| `atletas/templates/atletas/index.html` | OPERACIONAL | page | Sim | Sim | Não | Não |
| `atletas/templates/atletas/painel_organizacoes.html` | OPERACIONAL | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/perfil_atleta.html` | OPERACIONAL | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/lista_atletas.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/cadastrar_atleta.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/editar_atleta.html` | OPERACIONAL | page | Sim | Não | Sim | Não |
| `atletas/templates/atletas/importar_atletas.html` | OPERACIONAL | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/lista_academias.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/cadastrar_academia.html` | OPERACIONAL | page | Sim | Não | Sim | Não |
| `atletas/templates/atletas/editar_academia.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/deletar_academia.html` | OPERACIONAL | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/detalhe_academia.html` | OPERACIONAL | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/lista_campeonatos.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/cadastrar_campeonato.html` | OPERACIONAL | page | Sim | Não | Sim | Não |
| `atletas/templates/atletas/editar_campeonato.html` | OPERACIONAL | page | Sim | Não | Sim | Não |
| `atletas/templates/atletas/gerenciar_academias_campeonato.html` | OPERACIONAL | page | Sim | Não | Não | Não |
| `atletas/templates/atletas/lista_categorias.html` | OPERACIONAL | page | Sim | No/— | Não | Não |
| `atletas/templates/atletas/cadastrar_categoria.html` | OPERACIONAL | page | Sim | No/— | Não | Não |
| `atletas/templates/atletas/cadastrar_festival.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/tabela_categorias_peso.html` | ACADEMIA | page | Sim | Sim | Não | Não |
| `atletas/templates/atletas/pesagem.html` | PESAGEM | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/pesagem_mobile.html` | PESAGEM | mobile | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/lista_chaves.html` | OPERACIONAL | page | Sim | No/— | Não | Não |
| `atletas/templates/atletas/gerar_chave.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/gerar_chave_manual.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/detalhe_chave.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/imprimir_chave.html` | OPERACIONAL | print | Não | Sim | Não | Não |
| `atletas/templates/atletas/folha_chave_print.html` | OPERACIONAL | print | Não | Sim | Não | Não |
| `atletas/templates/atletas/folha_resultado_print.html` | OPERACIONAL | print | Não | Sim | Não | Não |
| `atletas/templates/atletas/folha_pesagem_print.html` | PESAGEM | print | Não | Sim | Não | Não |
| `atletas/templates/atletas/pdf_base.html` | (infra) | pdf | Não | Sim | Não | Não |
| `atletas/templates/atletas/academia/regulamento_pdf.html` | ACADEMIA | pdf | Não | No/— | No/— | Não |
| `atletas/templates/atletas/ajuda_manual.html` | INSTITUCIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/ajuda_manual_web.html` | INSTITUCIONAL | page | Não | Sim | No/— | Não |
| `atletas/templates/atletas/ranking_global.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/ranking_academias.html` | OPERACIONAL | page | Sim | Sim | No/— | Não |
| `atletas/templates/atletas/relatorios/dashboard.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/relatorios/chaves.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/relatorios/atletas_filtrados.html` | OPERACIONAL | page | No/— | No/— | No/— | Não |
| `atletas/templates/atletas/relatorios/atletas_inscritos.html` | OPERACIONAL | page | No/— | No/— | No/— | Não |
| `atletas/templates/atletas/relatorios/pesagem_final.html` | PESAGEM | page | No/— | No/— | No/— | Não |
| `atletas/templates/atletas/relatorios/resultados_categoria.html` | OPERACIONAL | page | No/— | No/— | No/— | Não |
| `atletas/templates/atletas/luta_mobile.html` | MESA | mobile | Não | Sim | No/— | Não |
| `atletas/templates/atletas/chave_mobile.html` | TELÃO | mobile | Não | Sim | No/— | Não |
| `atletas/templates/atletas/academia/painel.html` | ACADEMIA | page | Sim | Sim | No/— | No/— |
| `atletas/templates/atletas/academia/evento.html` | ACADEMIA | page | Sim | Sim | No/— | No/— |
| `atletas/templates/atletas/academia/cadastrar_atleta.html` | ACADEMIA | page | Sim | Sim | Sim | No/— |
| `atletas/templates/atletas/academia/lista_atletas.html` | ACADEMIA | page | Sim | Sim | No/— | No/— |
| `atletas/templates/atletas/academia/inscrever_atletas.html` | ACADEMIA | page | Sim | Sim | Sim | No/— |
| `atletas/templates/atletas/academia/ver_chaves.html` | ACADEMIA | page | Sim | Sim | No/— | No/— |
| `atletas/templates/atletas/academia/detalhe_chave.html` | ACADEMIA | page | Sim | Sim | No/— | No/— |
| `atletas/templates/atletas/administracao/painel.html` | OPERACIONAL | page | Sim | Sim | Sim | Não |
| `atletas/templates/atletas/administracao/gerenciar_usuarios.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/validar_pagamento.html` | OPERACIONAL | page | Sim | Sim | No/— | Não |
| `atletas/templates/atletas/administracao/ocorrencias_lista.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/ocorrencias_criar.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/ocorrencias_detalhe.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/ocorrencias_historico.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/conferencia_pagamentos_lista.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/conferencia_pagamentos_detalhe.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/conferencia_inscricoes.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/despesas.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/financeiro.html` | OPERACIONAL | page | Sim | Sim | No/— | Não |
| `atletas/templates/atletas/administracao/equipe.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/equipe_gerenciar.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/equipe_pessoas_lista.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/equipe_pessoas_elegiveis.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/gerenciar_senhas_campeonato.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/cadastros_operacionais.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/insumos.html` | OPERACIONAL | page | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/patrocinios.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/relatorios.html` | OPERACIONAL | page | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/operacional_card.html` | (infra) | partial | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/finance_card.html` | (infra) | partial | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/section_header.html` | (infra) | partial | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/kpi_card.html` | (infra) | partial | Sim | No/— | Sim | Não |
| `atletas/templates/atletas/administracao/partials/form_field.html` | (infra) | partial | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/dashboard_section.html` | (infra) | partial | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/mini_table.html` | (infra) | partial | Sim | No/— | No/— | Não |
| `atletas/templates/atletas/administracao/partials/dashboard_chart.html` | (infra) | partial | Sim | No/— | No/— | Não |

> Observação: alguns templates não apareceram no grep de `{% extends %}` (ex.: prints/mobile/pdf/standalone). Eles são os principais candidatos a “ilhas” visuais.

### 4.2 `competition_api` (17 templates)

| Caminho | Papel | Tipo | Bootstrap | CSS inline | JS inline | Tokens |
|---|---|---:|:---:|:---:|:---:|:---:|
| `competition_api/matches/templates/matches/base_public.html` | AUTH/INSTITUCIONAL | base | Sim | Não | Sim | Sim |
| `competition_api/matches/templates/matches/base_competition.html` | OPERACIONAL (comp) | base | Sim | Sim | Sim | Sim |
| `competition_api/matches/templates/matches/base_kiosk.html` | KIOSK (mesa/tv) | base | Sim | Sim | Sim | Sim |
| `competition_api/matches/templates/matches/public_landing.html` | AUTH/INSTITUCIONAL | page | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/ui/_tokens.html` | (infra) | component | Não | Sim | No/— | Sim |
| `competition_api/matches/templates/matches/_ui_styles.html` | (infra) | component | Não | Sim | No/— | Sim |
| `competition_api/matches/templates/matches/_filters.html` | OPERACIONAL (comp) | partial | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/components/match_card.html` | (infra) | component | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/components/status_badge.html` | (infra) | component | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/components/athlete_name.html` | (infra) | component | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/partials/match_row.html` | (infra) | partial | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/partials/flow_stepper.html` | (infra) | partial | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/partials/flow_stepper_item.html` | (infra) | partial | Sim | No/— | No/— | Sim |
| `competition_api/matches/templates/matches/acompanhamento.html` | TELÃO | page | Sim | Sim | Sim | Sim |
| `competition_api/matches/templates/matches/mesa.html` | MESA | page | Sim | Sim | Sim | Sim |
| `competition_api/matches/templates/matches/mesas.html` | OPERACIONAL (comp) | page | Sim | Sim | Sim | Sim |
| `competition_api/results/templates/results/oficiais.html` | OPERACIONAL (comp) | page | Sim | No/— | No/— | Sim |

---

## 5) Observações de risco (o que mais quebra em refactor)

- **A maior fonte de regressão é “dependência invisível” via base**:
  - páginas usando classes Bootstrap sem Bootstrap,
  - páginas usando classes “tokens/ui” sem tokens,
  - bases diferentes redefinindo `.container`, `.btn`, `.card` etc. (ex.: `academia/base_academia.html`).

- **Páginas standalone (mobile/print/pdf)** são “ilhas”:
  - têm CSS próprio e não herdam layout/estilo; qualquer unificação precisa ser muito gradual.

---

## 6) Próximo passo (aguardando validação)

Quando você aprovar este mapa:
- Eu sigo para **FASE 1 (Arquitetura — só texto)**, definindo bases por papel + design system mínimo sem Bootstrap, e o plano de strip **uma base por vez**, começando por **AUTH**.





