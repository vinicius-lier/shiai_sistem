# Auditoria de UX/Frontend (Templates Django) — SHIAI

**Escopo**: somente **templates HTML**, **CSS** e **JS simples** (quando existir nos templates).  
**Restrições absolutas respeitadas**:
- **NÃO** alterar `models`, `views`, `services`, endpoints, regras de domínio, permissões
- **NÃO** criar lógica de negócio em JS
- **NÃO** mudar fluxos funcionais nem remover telas
- **NÃO** implementar tempo real (WebSocket/HTMX) nem novos endpoints

**Objetivo**: inventariar todos os templates, classificar por **papel**, diagnosticar problemas de UX, e propor uma arquitetura base **somente em texto**, preparada para evolução.

---

## Resumo executivo

- **Total de templates HTML**: **107**
  - `atletas/…`: **93**
  - `competition_api/…`: **14**
  - `ranking_api/…`: **0**
- **Sinais positivos**
  - Existem “bases” e alguns **partials/components** já em uso (principalmente `administracao/partials` e `competition_api/matches/components`)
  - Há telas explicitamente pensadas para **ambiente real**: `*_mobile.html`, “TV/telão”, “mesa”
- **Riscos de UX mais críticos**
  - **Mistura de papéis** no mesmo layout/base (admin + mesa + telão)
  - **Densidade alta** em telas de evento ao vivo (pesagem/mesa/telão)
  - **Duplicação** (operacional vs academia) com alta chance de divergência visual e de microinterações
  - **Print/PDF** sem uma base tipográfica única (risco de inconsistência e baixa legibilidade)

---

## PARTE 1 — Auditoria por papel (visão operacional)

> A classificação detalhada **por template** (papel/tipo/uso/ambiente/risco) está no **Apêndice A**.  
> Aqui o foco é: **o que existe para cada papel** e quais telas são **críticas ao vivo**.

### 1.1 AUTH (Autenticação)
- **Objetivo**: entrada correta por papel, seleção de organização, troca de senha.
- **Ambiente**: notebook/celular.
- **Templates**
  - `atletas/templates/atletas/login_operacional.html` (page)
  - `atletas/templates/atletas/academia/login.html` (page)
  - `atletas/templates/atletas/academia/selecionar_login.html` (page)
  - `atletas/templates/atletas/selecionar_organizacao.html` (page)
  - `atletas/templates/atletas/alterar_senha_obrigatorio.html` (page)

### 1.2 PUBLIC (Institucional + Público/Telão)
- **Objetivo**: explicar o SHIAI, orientar acesso, exibir informações públicas e telas de telão.
- **Ambiente**: notebook/celular (institucional) e **TV/telão** (competição).
- **Templates**
  - Institucional:
    - `atletas/templates/atletas/landing.html` (page)
    - `atletas/templates/atletas/ajuda_manual.html` (page)
    - `atletas/templates/atletas/ajuda_manual_web.html` (page)
    - `atletas/templates/atletas/tabela_categorias_peso.html` (page)
  - Público/Telão (competition_api):
    - `competition_api/matches/templates/matches/acompanhamento.html` (page)
  - Público (legado em atletas):
    - `atletas/templates/atletas/chave_mobile.html` (mobile)
    - `atletas/templates/atletas/ranking_global.html` (page)
    - `atletas/templates/atletas/ranking_academias.html` (page)

### 1.3 OPERATIONAL (Operacional/Admin do evento)
- **Objetivo**: administrar evento, cadastros, inscrições, chaves, relatórios e financeiro.
- **Ambiente**: notebook (principal).
- **Templates (principais)**
  - Bases:
    - `atletas/templates/atletas/base.html` (base)
    - `atletas/templates/atletas/administracao/base_admin.html` (base)
  - Dashboards/Hubs:
    - `atletas/templates/atletas/index.html` (page)
    - `atletas/templates/atletas/administracao/painel.html` (page)
    - `atletas/templates/atletas/administracao/relatorios.html` (page)
  - Fluxo de evento (núcleo):
    - inscrições: `atletas/templates/atletas/inscrever_atletas.html`
    - chaves: `atletas/templates/atletas/lista_chaves.html`, `atletas/templates/atletas/gerar_chave.html`, `atletas/templates/atletas/gerar_chave_manual.html`, `atletas/templates/atletas/detalhe_chave.html`
  - Administrativo/Financeiro/Usuários:
    - `atletas/templates/atletas/administracao/financeiro.html`
    - `atletas/templates/atletas/administracao/validar_pagamento.html`
    - `atletas/templates/atletas/administracao/gerenciar_usuarios.html`
    - (demais telas em `atletas/templates/atletas/administracao/*.html`)

### 1.4 ACADEMY (Portal da Academia)
- **Objetivo**: cadastrar atletas, inscrever, acompanhar status e ver chaves.
- **Ambiente**: notebook/celular.
- **Templates**
  - Base:
    - `atletas/templates/atletas/academia/base_academia.html` (base)
  - Fluxo:
    - `atletas/templates/atletas/academia/painel.html`
    - `atletas/templates/atletas/academia/lista_atletas.html`
    - `atletas/templates/atletas/academia/cadastrar_atleta.html`
    - `atletas/templates/atletas/academia/inscrever_atletas.html`
    - `atletas/templates/atletas/academia/ver_chaves.html`
    - `atletas/templates/atletas/academia/detalhe_chave.html`
    - `atletas/templates/atletas/academia/regulamento_pdf.html` (pdf)

### 1.5 WEIGHING (Pesagem — crítico ao vivo)
- **Objetivo**: pesar rápido, tomar decisão (remanejar/desclassificar), manter fila fluida.
- **Ambiente**: notebook/tablet/celular + papel (prints).
- **Templates**
  - Telas:
    - `atletas/templates/atletas/pesagem.html` (page)
    - `atletas/templates/atletas/pesagem_mobile.html` (mobile)
  - Modais:
    - `atletas/templates/atletas/partials/modal_pesagem.html` (modal)
    - `atletas/templates/atletas/includes/pesagem_modal.html` (modal)
  - Print/relatório:
    - `atletas/templates/atletas/folha_pesagem_print.html` (print)
    - `atletas/templates/atletas/relatorios/pesagem_final.html` (page)

### 1.6 TABLE (Mesa — crítico ao vivo)
- **Objetivo**: registrar resultado e organizar lutas (fila por mesa).
- **Ambiente**: tablet/notebook (mesa), TV (consulta rápida), celular (legado).
- **Templates**
  - Competition API:
    - `competition_api/matches/templates/matches/base_kiosk.html` (base)
    - `competition_api/matches/templates/matches/mesa.html` (page)
    - `competition_api/matches/templates/matches/mesas.html` (page)
  - Legado:
    - `atletas/templates/atletas/luta_mobile.html` (mobile)

---

## PARTE 2 — Diagnóstico (problemas recorrentes de UX)

### 2.1 Mistura de papéis na mesma base
- `atletas/base.html` funciona como base “para tudo”, o que incentiva:
  - navegação exibindo itens de múltiplos papéis
  - estilos/estrutura de telas de ginásio herdando “tom administrativo”
- `competition_api/matches/base_competition.html` sugere casca “admin”, mas lista rotas que são de **TV/Mesa**, reforçando mistura de contexto.

### 2.2 Densidade alta em telas de evento ao vivo
- Pesagem, Mesa, TV/Telão precisam ser “modo ginásio”: **poucos elementos**, **alto contraste**, **ação principal óbvia**.
- Templates `*_mobile.html` indicam uso real — qualquer “adminidade” aumenta erro e tempo.

### 2.3 Falta de hierarquia visual consistente
Sintomas típicos (observáveis por padrão de projeto):
- tudo é card/título/botão no mesmo “peso”
- ações primárias e secundárias não se diferenciam consistentemente
- falta padrão visual para responder:
  - **Onde estou?**
  - **O que posso fazer aqui?**
  - **Qual o próximo passo natural?**

### 2.4 Duplicação Operacional vs Academia
Há duplicação explícita de telas e fluxos:
- cadastro/lista de atletas
- inscrição
- visualização de chaves (detalhe)

Risco: divergência de layout, mensagens, botões e microinterações ao longo do tempo.

### 2.5 Modais críticos sem padrão global
- Pesagem tem duplicação `includes/` vs `partials/`, o que normalmente gera:
  - botões com textos/ordem diferentes
  - estados visuais diferentes (salvando/erro/sucesso)

### 2.6 Print/PDF sem padronização tipográfica única
Sem uma base de impressão consistente, surgem:
- tamanhos de fonte e margens inconsistentes
- tabelas “quebrando” diferente por página
- baixa legibilidade no mundo físico

### 2.7 JS frágil (risco estrutural)
Risco típico em templates: JS que depende de:
- seletores frágeis (classes genéricas, estrutura de DOM instável)
- múltiplas versões de comportamento por tela

Mesmo sem alterar backend, isso pode ser mitigado no futuro com **IDs semânticos estáveis** e containers definidos.

---

## PARTE 3 — Proposta de arquitetura de layout (sem codar)

### 3.1 Bases sugeridas (conceito)

#### `base_public.html` (Institucional + Público/Telão quando aplicável)
- **Header**: marca + CTA “Entrar”
- **Sem sidebar**
- **Informação permitida**: somente informativo, sem dados sensíveis
- **Tom visual**: produto (limpo, convidativo)

#### `base_auth.html` (Autenticação)
- **Header mínimo** (logo + voltar)
- **Sem sidebar**
- **Informação**: login/seleção/troca senha
- **Tom**: clareza e redução de erro

#### `base_operational.html` (Operacional)
- **Header/topbar**: evento ativo + status + usuário/role + sair
- **Sidebar**: fluxo do evento (Evento → Inscrições → Pesagem → Chaves → Lutas → Resultados → Ranking) + itens administrativos
- **Informação**: alta, mas com hierarquia rígida (KPI > listas > detalhes)
- **Tom**: administrativo orientado a fluxo

#### `base_academy.html` (Academia)
- **Header**: academia + evento/contexto
- **Sidebar reduzida**: Atletas, Inscrições, Status/Resultados
- **Informação**: baixa/média; sem itens operacionais
- **Tom**: autoatendimento, guiado

#### `base_weighing.html` (Pesagem — crítico ao vivo)
- **Header**: Pesagem + evento + filtros essenciais
- **Sem sidebar** (ou mínima)
- **Informação**: mínimo necessário para pesar/decidir
- **Tom**: ginásio, foco, anti-erro

#### `base_table.html` (Mesa — kiosk mode)
- **Kiosk**: sem sidebar; navegação mínima (Mesa #, TV, sair)
- **Informação**: mínimo necessário para registrar resultado
- **Tom**: ginásio, anti-erro, foco na luta atual/próxima

---

## PARTE 4 — Componentes de UI (conceituais, sem implementar)

### 4.1 Cards
- **KPI Card**: número grande + label + delta/nota
- **Action Card**: CTA primário + explicação curta
- **Status Card**: estado do fluxo (pesagem %, chaves geradas, lutas em andamento)

### 4.2 Badges de status (mapa único de cores)
- **SCHEDULED**: azul claro (informação/pendente)
- **FINISHED**: verde (concluído)
- **WO/WALKOVER**: laranja/amarelo (atenção)
- **BLOCKED/DISQUALIFIED**: vermelho (bloqueio)
- **INFO**: cinza/azul neutro (apoio)

### 4.3 Tabelas padrão
- cabeçalho consistente
- colunas essenciais por papel (academia ≠ operacional)
- ações sempre no mesmo lugar (coluna final)

### 4.4 Modais críticos
- confirmar (ações destrutivas)
- registrar (resultado/peso)
- alerta (fora da faixa / bloqueio)
- **ordem e cor dos botões padronizadas**

### 4.5 Alertas
- sucesso / erro / aviso / info com padrão único (tamanho, ícone, margem)

### 4.6 Flow Stepper do evento
- Inscrição → Pesagem → Chaves → Lutas → Resultados
- passo atual sempre destacado
- objetivo: reforçar “competição é um fluxo”

---

## PARTE 5 — Roadmap de evolução (sem backend)

### Fase 1 — Padronização visual mínima (sem quebrar nada)
- Definir tokens únicos (tipografia, espaçamento, cores)
- Padronizar `page-head` (título, subtítulo, ação primária)
- Padronizar badges/alerts e botões (primário/segundário/perigo)
- Padronizar print/PDF com uma base tipográfica

### Fase 2 — Separação clara por papel
- Cada papel herda sua base:
  - operational / academy / weighing / table / public / auth
- Navegação enxuta por contexto (sumir o que não é do papel)
- Reduzir duplicações visuais (mesmo padrão de UI em telas duplicadas)

### Fase 3 — Preparação para tempo real (somente preparar, não implementar)
- Containers semânticos estáveis (`#matches-table`, `#mesa-queue`, `#acompanhamento-board` etc.)
- IDs estáveis e DOM previsível (JS menos frágil)
- Comentários de pontos futuros de integração (HTMX/WebSocket), sem adicionar dependências

---

## APÊNDICE A — Inventário completo de templates (107)

### Legenda dos campos

- **Papel**: Autenticação / Institucional / Operacional / Academia / Pesagem / Mesa / Público-Telão
- **Tipo**: `page | base | partial | component | modal | print | mobile | pdf`
- **Uso**: **Crítico ao vivo** / **Administrativo** / **Informativo**
- **Ambiente**: Notebook / Tablet / Celular / TV-Telão / Papel(PDF/Print)
- **Risco UX**: baixo / médio / alto (probabilidade de erro/atrito operacional, legibilidade, confusão de papel)
- **Duplicação provável**: sim/não (quando há versões paralelas em Operacional vs Academia, ou include/partial duplicado)

> Nota metodológica: nesta etapa a classificação é majoritariamente **inferida por caminho/nome** do template. Uma auditoria “pixel-perfect” exige leitura individual, mas esta visão já é suficiente para uma reestruturação por bases/roles.

### A.1 — `competition_api/` (14)

| Caminho | Tela sugerida | App | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|---|
| `competition_api/matches/templates/matches/base_competition.html` | Base “Admin” Competition | competition_api.matches | Operacional | base | Administrativo | Notebook | **alto** | não | Mistura navegação “admin” com rotas de TV/Mesa; tende a confundir papéis |
| `competition_api/matches/templates/matches/base_kiosk.html` | Base Kiosk (TV/Mesa) | competition_api.matches | Público-Telão | base | Crítico ao vivo | TV-Telão/Tablet | médio | não | Kiosk mode é correto; deve evitar “admin vibe” e excesso de controles |
| `competition_api/matches/templates/matches/acompanhamento.html` | Acompanhamento (TV/Telão) | competition_api.matches | Público-Telão | page | Crítico ao vivo | TV-Telão | **alto** | não | Precisa hierarquia extrema (atual > próximas > recentes) e legibilidade a distância |
| `competition_api/matches/templates/matches/mesa.html` | Mesa (Registrar Resultado) | competition_api.matches | Mesa | page | Crítico ao vivo | Tablet/Notebook | **alto** | não | Tela sensível a erro humano; ação primária deve dominar |
| `competition_api/matches/templates/matches/mesas.html` | Organização de Mesas | competition_api.matches | Mesa | page | Crítico ao vivo | Notebook/Tablet | médio | não | Operação visual; precisa prevenir duplicação/ruído e manter foco na fila |
| `competition_api/results/templates/results/oficiais.html` | Resultados Oficiais | competition_api.results | Operacional | page | Administrativo | Notebook | médio | não | Tela de “fechamento”; deve comunicar bloqueios/pending de forma inequívoca |
| `competition_api/matches/templates/matches/_ui_styles.html` | Estilos compartilhados | competition_api.matches | Operacional | partial | Administrativo | — | médio | não | Centralização boa; precisa alinhar com design system do legado (`atletas/base`) |
| `competition_api/matches/templates/matches/_filters.html` | Filtros (parcial) | competition_api.matches | Operacional | partial | Administrativo | — | baixo | não | Reuso positivo; atenção à consistência com filtros do legado |
| `competition_api/matches/templates/matches/components/status_badge.html` | Badge de Status | competition_api.matches | Mesa | component | Crítico ao vivo | — | baixo | não | Base para consistência do mapa de cores |
| `competition_api/matches/templates/matches/components/athlete_name.html` | Nome do Atleta (azul/branco) | competition_api.matches | Mesa | component | Crítico ao vivo | — | baixo | não | Ajuda a fixar identidade “azul/branco” |
| `competition_api/matches/templates/matches/components/match_card.html` | Card de Luta | competition_api.matches | Mesa | component | Crítico ao vivo | — | baixo | não | Excelente bloco padrão (mesa/tv/mesas) |
| `competition_api/matches/templates/matches/partials/match_row.html` | Linha de Luta | competition_api.matches | Público-Telão | partial | Crítico ao vivo | — | baixo | não | Permite padronizar render de luta nas 3 telas |
| `competition_api/matches/templates/matches/partials/flow_stepper.html` | Stepper do Fluxo | competition_api.matches | Operacional | partial | Administrativo | — | médio | não | Conceito certo; precisa ser “bulletproof” e estável |
| `competition_api/matches/templates/matches/partials/flow_stepper_item.html` | Item do Stepper | competition_api.matches | Operacional | partial | Administrativo | — | médio | não | Helper; deve ser mínimo para evitar fragilidade |

### A.2 — `atletas/` (93)

#### A.2.1 — Bases / Institucional / Autenticação

| Caminho | Tela sugerida | App | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/base.html` | Base Global | atletas | Operacional | base | Administrativo | Notebook | **alto** | sim | Base grande e “tudo em um”; forte chance de misturar papéis na navegação |
| `atletas/templates/atletas/landing.html` | Landing Pública | atletas | Institucional | page | Informativo | Notebook/Celular | médio | não | Precisa orientar login por papel e explicar o sistema sem dados sensíveis |
| `atletas/templates/atletas/login_operacional.html` | Login Operacional | atletas | Autenticação | page | Administrativo | Notebook/Celular | médio | sim | Porta de entrada; deve ser simples e inequívoca (qual login usar) |
| `atletas/templates/atletas/academia/login.html` | Login Academia | atletas | Autenticação | page | Administrativo | Notebook/Celular | médio | sim | Duplicação com login operacional: risco de estilos divergentes |
| `atletas/templates/atletas/academia/selecionar_login.html` | Seleção de Login | atletas | Autenticação | page | Administrativo | Notebook/Celular | médio | não | Ajuda a separar papéis, mas precisa ser “óbvio” e direto |
| `atletas/templates/atletas/selecionar_organizacao.html` | Selecionar Organização | atletas | Autenticação | page | Administrativo | Notebook/Celular | médio | não | Se não explicar contexto, parece etapa burocrática |
| `atletas/templates/atletas/alterar_senha_obrigatorio.html` | Troca de Senha Obrigatória | atletas | Autenticação | page | Administrativo | Notebook/Celular | **alto** | não | Fricção inevitável; UX deve reduzir erro e tempo |
| `atletas/templates/atletas/ajuda_manual.html` | Manual/Ajuda | atletas | Institucional | page | Informativo | Notebook/Celular | médio | sim | Conteúdo longo tende a ficar denso sem sumário e seções |
| `atletas/templates/atletas/ajuda_manual_web.html` | Manual/Ajuda (web) | atletas | Institucional | page | Informativo | Notebook/Celular | médio | sim | Duplicação com manual: sinal de falta de base/componentização |
| `atletas/templates/atletas/tabela_categorias_peso.html` | Tabela de Categorias | atletas | Institucional | page | Informativo | Notebook/Celular | baixo | não | Boa para consulta; precisa tipografia legível e contraste |

#### A.2.2 — Operacional (evento/admin)

| Caminho | Tela sugerida | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/index.html` | Dashboard Operacional | Operacional | page | Administrativo | Notebook | **alto** | não | Dashboard pode virar “tudo nível 1”; precisa hierarquia de KPIs/ações |
| `atletas/templates/atletas/painel_organizacoes.html` | Painel Organizações | Operacional | page | Administrativo | Notebook | médio | não | “Onde estou” e contexto multi-org precisam ser óbvios |
| `atletas/templates/atletas/metricas_evento.html` | Métricas do Evento | Operacional | page | Administrativo | Notebook | médio | não | Métricas podem virar ruído sem destaque do crítico |
| `atletas/templates/atletas/lista_campeonatos.html` | Campeonatos (lista) | Operacional | page | Administrativo | Notebook | médio | não | Lista admin; risco de ações dispersas e filtros fracos |
| `atletas/templates/atletas/cadastrar_campeonato.html` | Criar Campeonato | Operacional | page | Administrativo | Notebook | médio | não | Form longo precisa agrupamento visual (seções) |
| `atletas/templates/atletas/editar_campeonato.html` | Editar Campeonato | Operacional | page | Administrativo | Notebook | médio | sim | Duplicação com “criar” pode divergir em layout/feedback |
| `atletas/templates/atletas/lista_academias.html` | Academias (lista) | Operacional | page | Administrativo | Notebook | médio | sim | CRUD; ações principais/ secundárias devem ser visuais e consistentes |
| `atletas/templates/atletas/cadastrar_academia.html` | Criar Academia | Operacional | page | Administrativo | Notebook | médio | sim | Duplicação com “editar” |
| `atletas/templates/atletas/editar_academia.html` | Editar Academia | Operacional | page | Administrativo | Notebook | médio | sim | Duplicação com “criar” |
| `atletas/templates/atletas/deletar_academia.html` | Excluir Academia (confirmar) | Operacional | page | Administrativo | Notebook | **alto** | não | Confirmação deve ser inequívoca e sem distrações |
| `atletas/templates/atletas/detalhe_academia.html` | Academia (detalhe) | Operacional | page | Administrativo | Notebook | médio | sim | Pode ficar enciclopédico; precisa “próximo passo” claro |
| `atletas/templates/atletas/lista_atletas.html` | Atletas (lista) | Operacional | page | Administrativo | Notebook | médio | sim | Tabela densa provável; risco de baixa legibilidade |
| `atletas/templates/atletas/cadastrar_atleta.html` | Criar Atleta (operacional) | Operacional | page | Administrativo | Notebook | médio | **sim** | Duplicado com `academia/cadastrar_atleta.html` |
| `atletas/templates/atletas/editar_atleta.html` | Editar Atleta (operacional) | Operacional | page | Administrativo | Notebook | médio | **sim** | Duplicado por fluxo; risco de inconsistência |
| `atletas/templates/atletas/importar_atletas.html` | Importar Atletas | Operacional | page | Administrativo | Notebook | **alto** | não | Upload/erros precisam feedback forte e hierarquia clara |
| `atletas/templates/atletas/lista_categorias.html` | Categorias (lista) | Operacional | page | Administrativo | Notebook | médio | não | Admin |
| `atletas/templates/atletas/cadastrar_categoria.html` | Criar Categoria | Operacional | page | Administrativo | Notebook | médio | sim | Duplicação com edições futuras (se existirem) |
| `atletas/templates/atletas/cadastrar_festival.html` | Criar Festival | Operacional | page | Administrativo | Notebook | médio | não | Tela específica; risco de confusão com “classe/categoria” |
| `atletas/templates/atletas/inscrever_atletas.html` | Inscrições (operacional) | Operacional | page | Administrativo | Notebook | **alto** | **sim** | Duplicado com `academia/inscrever_atletas.html`; fluxo longo pede checkpoints |
| `atletas/templates/atletas/gerenciar_academias_campeonato.html` | Academias no Evento | Operacional | page | Administrativo | Notebook | médio | não | Operação do evento; pode virar “tela tabela” |
| `atletas/templates/atletas/lista_chaves.html` | Chaves (lista) | Operacional | page | Administrativo | Notebook | **alto** | sim | Núcleo do fluxo; precisa status visual por categoria/classe |
| `atletas/templates/atletas/gerar_chave.html` | Gerar Chaves | Operacional | page | Administrativo | Notebook | **alto** | não | Ação crítica; alertas e confirmação devem dominar |
| `atletas/templates/atletas/gerar_chave_manual.html` | Gerar Chaves (manual) | Operacional | page | Administrativo | Notebook | **alto** | não | Poder alto = UX anti-erro (sem “cliques perigosos”) |
| `atletas/templates/atletas/detalhe_chave.html` | Chave (detalhe) | Operacional | page | Administrativo | Notebook | médio | **sim** | Versão academia também existe; risco de layout divergente |
| `atletas/templates/atletas/imprimir_chave.html` | Imprimir Chave | Operacional | page | Administrativo | Notebook | baixo | não | Ponte para impressão |
| `atletas/templates/atletas/perfil_atleta.html` | Perfil do Atleta | Operacional | page | Administrativo | Notebook/Celular | médio | sim | Perfil tende a crescer e ficar denso sem seções |

#### A.2.3 — Pesagem (crítico ao vivo) + modais + impressão

| Caminho | Tela sugerida | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/pesagem.html` | Pesagem | Pesagem | page | **Crítico ao vivo** | Notebook/Tablet | **alto** | sim | Precisa “sem distração”; estados/alertas determinam velocidade |
| `atletas/templates/atletas/pesagem_mobile.html` | Pesagem (mobile) | Pesagem | mobile | **Crítico ao vivo** | Celular | **alto** | sim | Mobile exige botões grandes e fluxo curtíssimo |
| `atletas/templates/atletas/partials/modal_pesagem.html` | Modal Pesagem | Pesagem | modal | **Crítico ao vivo** | Notebook/Tablet | **alto** | **sim** | Existe também `includes/pesagem_modal.html` (duplicação) |
| `atletas/templates/atletas/includes/pesagem_modal.html` | Modal Pesagem (include) | Pesagem | modal | **Crítico ao vivo** | Notebook/Tablet | **alto** | **sim** | Duplicação sugere inconsistência inevitável |
| `atletas/templates/atletas/folha_pesagem_print.html` | Folha Pesagem (print) | Pesagem | print | Crítico ao vivo | Papel(Print) | médio | não | Print precisa tipografia e grid próprios |
| `atletas/templates/atletas/relatorios/pesagem_final.html` | Relatório Pesagem Final | Pesagem | page | Administrativo | Notebook | médio | não | Relatório pós-evento; densidade moderada |

#### A.2.4 — Academia

| Caminho | Tela sugerida | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/academia/base_academia.html` | Base Academia | Academia | base | Administrativo | Notebook/Celular | **alto** | sim | Base grande e separada do operacional → divergência provável |
| `atletas/templates/atletas/academia/painel.html` | Dashboard Academia | Academia | page | Administrativo | Notebook/Celular | **alto** | não | Deve ser simples; risco de herdar densidade “admin” |
| `atletas/templates/atletas/academia/evento.html` | Evento (academia) | Academia | page | Administrativo | Notebook/Celular | médio | não | “Onde estou / próximo passo” precisa ficar óbvio |
| `atletas/templates/atletas/academia/lista_atletas.html` | Atletas (academia) | Academia | page | Administrativo | Notebook/Celular | médio | **sim** | Duplicado com lista operacional |
| `atletas/templates/atletas/academia/cadastrar_atleta.html` | Criar Atleta (academia) | Academia | page | Administrativo | Notebook/Celular | médio | **sim** | Duplicado com operacional |
| `atletas/templates/atletas/academia/inscrever_atletas.html` | Inscrições (academia) | Academia | page | Administrativo | Notebook/Celular | **alto** | **sim** | Duplicado com operacional; fluxo longo sem checkpoints cansa |
| `atletas/templates/atletas/academia/ver_chaves.html` | Ver Chaves | Academia | page | Informativo | Notebook/Celular | médio | sim | Read-only deve parecer “acompanhamento”, não “admin” |
| `atletas/templates/atletas/academia/detalhe_chave.html` | Chave (detalhe) | Academia | page | Informativo | Notebook/Celular | médio | **sim** | Duplicado com `atletas/detalhe_chave.html` |
| `atletas/templates/atletas/academia/regulamento_pdf.html` | Regulamento (PDF) | Academia | pdf | Informativo | Papel(PDF) | baixo | não | PDF precisa base tipográfica consistente |

#### A.2.5 — Mesa + Público/Telão (legado em atletas)

| Caminho | Tela sugerida | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/luta_mobile.html` | Luta (mobile/mesa legado) | Mesa | mobile | **Crítico ao vivo** | Tablet/Celular | **alto** | sim | Existe “mesa” moderna no `competition_api`; identidade pode divergir |
| `atletas/templates/atletas/chave_mobile.html` | Chave (mobile) | Público-Telão | mobile | Crítico ao vivo | Celular | médio | sim | Deve ser legível e 100% read-only |
| `atletas/templates/atletas/ranking_global.html` | Ranking Global | Público-Telão | page | Informativo | TV-Telão/Notebook | médio | não | Ranking precisa visual de telão, não tabela fria |
| `atletas/templates/atletas/ranking_academias.html` | Ranking Academias | Público-Telão | page | Informativo | TV-Telão/Notebook | médio | não | Idem |

#### A.2.6 — Relatórios / Print / PDF

| Caminho | Tela sugerida | Papel | Tipo | Uso | Ambiente | Risco UX | Duplicação provável | Observações rápidas |
|---|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/pdf_base.html` | Base PDF | Operacional | pdf | Administrativo | Papel(PDF) | médio | não | Sem base única, PDFs divergem (tipografia, margens, tabelas) |
| `atletas/templates/atletas/folha_chave_print.html` | Folha Chave (print) | Operacional | print | Crítico ao vivo | Papel(Print) | médio | não | Print precisa grid e tipografia consistentes |
| `atletas/templates/atletas/folha_resultado_print.html` | Folha Resultado (print) | Operacional | print | Crítico ao vivo | Papel(Print) | médio | não | Idem |
| `atletas/templates/atletas/relatorios/dashboard.html` | Relatório: Dashboard | Operacional | page | Administrativo | Notebook | médio | não | Relatórios tendem a repetir layout sem base |
| `atletas/templates/atletas/relatorios/chaves.html` | Relatório: Chaves | Operacional | page | Administrativo | Notebook | médio | não | Denso |
| `atletas/templates/atletas/relatorios/atletas_inscritos.html` | Relatório: Atletas Inscritos | Operacional | page | Administrativo | Notebook | médio | não | Denso |
| `atletas/templates/atletas/relatorios/atletas_filtrados.html` | Relatório: Atletas Filtrados | Operacional | page | Administrativo | Notebook | médio | não | Denso |
| `atletas/templates/atletas/relatorios/resultados_categoria.html` | Relatório: Resultados por Categoria | Operacional | page | Informativo | Notebook/TV-Telão | médio | não | Poderia ser telão; hoje está em formato de relatório |

#### A.2.7 — Administração (`administracao/…`) + partials

**Regra geral**: `administracao/*.html` → **Operacional**, `page`, **Administrativo**, risco **médio** (alguns **altos** quando envolvem validação/finanças/usuários).

| Caminho | Tela sugerida | Papel | Tipo | Uso | Ambiente | Risco UX | Observações rápidas |
|---|---|---|---|---|---|---|---|
| `atletas/templates/atletas/administracao/base_admin.html` | Base Admin | Operacional | base | Administrativo | Notebook | **alto** | Base “wrapper”; não define casca operacional dedicada (topbar/sidebar/fluxo) |
| `atletas/templates/atletas/administracao/painel.html` | Painel Administração | Operacional | page | Administrativo | Notebook | **alto** | Painel precisa hierarquia forte (o que é crítico vs secundário) |
| `atletas/templates/atletas/administracao/financeiro.html` | Financeiro | Operacional | page | Administrativo | Notebook | **alto** | Densidade inevitável; precisa seções claras e actions seguras |
| `atletas/templates/atletas/administracao/despesas.html` | Despesas | Operacional | page | Administrativo | Notebook | médio | CRUD + tabelas |
| `atletas/templates/atletas/administracao/patrocinios.html` | Patrocínios | Operacional | page | Administrativo | Notebook | médio | Admin |
| `atletas/templates/atletas/administracao/insumos.html` | Insumos | Operacional | page | Administrativo | Notebook | médio | Admin |
| `atletas/templates/atletas/administracao/relatorios.html` | Relatórios (hub) | Operacional | page | Administrativo | Notebook | médio | Hub deve ser enxuto; risco de lista longa e sem agrupamento |
| `atletas/templates/atletas/administracao/conferencia_inscricoes.html` | Conferência Inscrições | Operacional | page | Administrativo | Notebook | **alto** | Validação humana: UX anti-erro é crítica |
| `atletas/templates/atletas/administracao/conferencia_pagamentos_lista.html` | Conferência Pagamentos (lista) | Operacional | page | Administrativo | Notebook | **alto** | Tabela densa + decisões: risco alto de clique errado |
| `atletas/templates/atletas/administracao/conferencia_pagamentos_detalhe.html` | Conferência Pagamentos (detalhe) | Operacional | page | Administrativo | Notebook | **alto** | “Próximo passo” precisa estar explícito |
| `atletas/templates/atletas/administracao/validar_pagamento.html` | Validar Pagamento | Operacional | page | Administrativo | Notebook | **alto** | Ação sensível: confirmação e hierarquia fortes |
| `atletas/templates/atletas/administracao/equipe.html` | Equipe (hub) | Operacional | page | Administrativo | Notebook | médio | Gestão de pessoas tende a fragmentar |
| `atletas/templates/atletas/administracao/equipe_gerenciar.html` | Gerenciar Equipe | Operacional | page | Administrativo | Notebook | médio | CRUD |
| `atletas/templates/atletas/administracao/equipe_pessoas_lista.html` | Pessoas (lista) | Operacional | page | Administrativo | Notebook | médio | Denso |
| `atletas/templates/atletas/administracao/equipe_pessoas_elegiveis.html` | Pessoas elegíveis | Operacional | page | Administrativo | Notebook | médio | Seleção precisa feedback claro |
| `atletas/templates/atletas/administracao/gerenciar_senhas_campeonato.html` | Senhas do Evento | Operacional | page | Administrativo | Notebook | **alto** | Tela crítica; erro operacional aqui é caro |
| `atletas/templates/atletas/administracao/gerenciar_usuarios.html` | Gerenciar Usuários | Operacional | page | Administrativo | Notebook | **alto** | Papéis/roles exigem clareza e prevenção de erro |
| `atletas/templates/atletas/administracao/cadastros_operacionais.html` | Cadastros Operacionais | Operacional | page | Administrativo | Notebook | médio | Hub; sem navegação clara vira lista caótica |
| `atletas/templates/atletas/administracao/ocorrencias_lista.html` | Ocorrências (lista) | Operacional | page | Administrativo | Notebook | médio | Precisa status/badges consistentes |
| `atletas/templates/atletas/administracao/ocorrencias_detalhe.html` | Ocorrência (detalhe) | Operacional | page | Administrativo | Notebook | médio | Ação/status devem estar destacados |
| `atletas/templates/atletas/administracao/ocorrencias_criar.html` | Criar Ocorrência | Operacional | page | Administrativo | Notebook | médio | Form |
| `atletas/templates/atletas/administracao/ocorrencias_historico.html` | Histórico Ocorrências | Operacional | page | Administrativo | Notebook | médio | Log denso |
| `atletas/templates/atletas/administracao/partials/dashboard_chart.html` | Partial: gráfico dashboard | Operacional | partial | Administrativo | — | baixo | Bom sinal de componentização local |
| `atletas/templates/atletas/administracao/partials/dashboard_section.html` | Partial: seção dashboard | Operacional | partial | Administrativo | — | baixo | Ajuda hierarquia (se usado consistentemente) |
| `atletas/templates/atletas/administracao/partials/finance_card.html` | Partial: card financeiro | Operacional | partial | Administrativo | — | baixo | Candidato a design system |
| `atletas/templates/atletas/administracao/partials/form_field.html` | Partial: campo de form | Operacional | partial | Administrativo | — | baixo | Base perfeita para padronizar formulários |
| `atletas/templates/atletas/administracao/partials/kpi_card.html` | Partial: KPI | Operacional | partial | Administrativo | — | baixo | KPI precisa consistência de tamanho/contraste |
| `atletas/templates/atletas/administracao/partials/mini_table.html` | Partial: mini tabela | Operacional | partial | Administrativo | — | baixo | Boa para dashboards, risco baixo |
| `atletas/templates/atletas/administracao/partials/operacional_card.html` | Partial: card operacional | Operacional | partial | Administrativo | — | baixo | Bloco padrão útil |
| `atletas/templates/atletas/administracao/partials/section_header.html` | Partial: cabeçalho seção | Operacional | partial | Administrativo | — | baixo | Ajuda responder “onde estou” dentro da página |

---

## APÊNDICE B — Observações específicas (alvos fáceis de padronização)

- **`atletas/templates/atletas/administracao/partials/form_field.html`**: já indica um caminho bom para padronizar formulários.
- **`competition_api/matches/templates/matches/components/*`**: “componentização” boa para padronizar mesa/telão/mesas.
- **Pesagem modal duplicado** (`partials/` vs `includes/`): risco alto de divergência; idealmente convergir para **1** padrão no futuro (sem mudar fluxo).


