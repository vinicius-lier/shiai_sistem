# Auditoria de Estilos – SHIAI

Data: 2025-12-28

## Escopo
- Templates em `atletas/templates/atletas` e layouts em `atletas/templates/atletas/layouts`.
- Includes de UI em `atletas/templates/atletas/ui`.
- Landing pública em `atletas/templates/atletas/landing.html`.

## Visao geral
O sistema possui **mais de uma linguagem visual** em paralelo:
- `atletas/templates/atletas/base.html` concentra um design legado (tokens, navbar, sidebar, CSS inline grande).
- `atletas/templates/atletas/layouts/base_operational.html` + `atletas/templates/atletas/ui/*` formam um **design system novo** (tokens, helpers, components), mas ainda com muito CSS inline nas telas.
- `atletas/templates/atletas/landing.html` usa **Tailwind CDN**, criando um terceiro estilo independente.

Isso gera inconsistencias visuais, bugs de navbar/dropdown e dificulta manutencao.

---

## Principais achados (com gravidade)

### Alta
1) **Dois (ou mais) design systems concorrendo**
   - `atletas/templates/atletas/base.html` define tokens, componentes, navbar e sidebar proprios.
   - `atletas/templates/atletas/layouts/base_operational.html` usa `ui/_tokens.html`, `ui/_components.html`, `ui/_helpers.html`.
   - Impacto: inconsistencias visuais e regressao de estilos ao trocar layout.

2) **CSS inline massivo nos templates**
   - Ex.: `atletas/templates/atletas/index.html`, `atletas/templates/atletas/detalhe_academia.html`, `atletas/templates/atletas/academia/painel.html`.
   - Impacto: estilos dificeis de manter, pouca reutilizacao e divergencia entre telas.

3) **Frameworks misturados na mesma base**
   - Bootstrap 5.3.2 em `atletas/templates/atletas/base.html`.
   - Bootstrap 5.3.0 em `atletas/templates/atletas/layouts/base_operational.html`.
   - Tailwind CDN em `atletas/templates/atletas/landing.html`.
   - Impacto: conflitos de classes, tamanhos e comportamento de componentes.

### Media
4) **Fonts carregadas de forma inconsistente**
   - `base.html` e `landing.html` carregam Inter via Google Fonts.
   - `base_operational.html` usa Inter nos tokens, mas nao carrega a fonte.
   - Impacto: renderizacao divergente entre telas operacionais.

5) **Duplicacao de estilos para navbar**
   - `base.html` tem CSS dedicado a `.navbar-shiai`.
   - `ui/_components.html` passou a ter estilos proprios para dropdown.
   - Impacto: comportamento diferente dependendo do layout usado.

6) **Tokens duplicados e sem consolidacao**
   - `base.html` define seus proprios `--color-*`, `--spacing-*`.
   - `ui/_tokens.html` define `--primary`, `--surface` e aliases.
   - Impacto: confusion entre tokens e risco de usar o token errado.

### Baixa
7) **Uso extensivo de estilos inline para responsividade**
   - Muitos ajustes de grid/flex em `style=...` nos templates.
   - Impacto: manutencao dificil, pouca padronizacao responsiva.

8) **Padroes diferentes para botoes e cards**
   - `.btn` e `.card` existem em `ui/_components.html`, mas telas legadas usam overrides inline.

---

## Correcoes recomendadas (plano)

### Fase 1 – Estabilizacao rapida
- Definir **um layout padrao** para o operacional:
  - Preferir `atletas/templates/atletas/layouts/base_operational.html`.
  - Evitar novo CSS no `base.html` (legado).
- Unificar versao do Bootstrap (escolher 5.3.2 ou 5.3.0 e padronizar).
- Carregar fonte Inter em **todos** os layouts (ex.: em `ui/_tokens.html` ou via include global).

### Fase 2 – Consolidacao de estilos
- Migrar estilos inline repetidos para classes reutilizaveis em `ui/_components.html` ou `ui/_helpers.html`.
- Criar classes utilitarias para:
  - Grids comuns (2, 3, 4 colunas)
  - Cards com header gradient
  - Tabelas padronizadas
  - Badges e status
- Eliminar estilos inline em telas chave:
  - `atletas/templates/atletas/index.html`
  - `atletas/templates/atletas/academia/painel.html`
  - `atletas/templates/atletas/detalhe_academia.html`
  - `atletas/templates/atletas/lista_academias.html`

### Fase 3 – Harmonizacao visual
- Unificar paleta de cores (tokens unicos).
- Consolidar tipografia (um unico `--font-family`).
- Definir escala unica de espacamento e radius.

---

## Lista de arquivos prioritarios para correcoes

- Layouts
  - `atletas/templates/atletas/base.html`
  - `atletas/templates/atletas/layouts/base_operational.html`
  - `atletas/templates/atletas/layouts/base_academy.html`
  - `atletas/templates/atletas/layouts/base_public.html`

- UI System
  - `atletas/templates/atletas/ui/_tokens.html`
  - `atletas/templates/atletas/ui/_components.html`
  - `atletas/templates/atletas/ui/_helpers.html`

- Telas com maior uso de inline style
  - `atletas/templates/atletas/index.html`
  - `atletas/templates/atletas/academia/painel.html`
  - `atletas/templates/atletas/detalhe_academia.html`
  - `atletas/templates/atletas/lista_academias.html`
  - `atletas/templates/atletas/gerenciar_academias_campeonato.html`

---

## Proximos passos sugeridos
1) Escolher qual layout sera o oficial (legado vs operacional novo).
2) Remover dependencia do layout que nao for usado.
3) Criar um backlog de componentes reutilizaveis.
4) Migrar 3-5 telas por ciclo, removendo inline CSS.

