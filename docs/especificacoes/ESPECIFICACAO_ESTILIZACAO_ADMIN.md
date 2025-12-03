# 📋 ESPECIFICAÇÃO COMPLETA DE ESTILIZAÇÃO
## Módulo Administrativo SHIAI SISTEM

---

## 🔷 1. PADRONIZAÇÃO GLOBAL OBRIGATÓRIA

### 1.1 Tipografia

**Fonte Base:**
- **Família:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Tamanhos (CSS Variables):**
  - `--font-size-xs`: 0.75rem (12px)
  - `--font-size-sm`: 0.875rem (14px)
  - `--font-size-base`: 1rem (16px)
  - `--font-size-lg`: 1.125rem (18px)
  - `--font-size-xl`: 1.25rem (20px)
  - `--font-size-2xl`: 1.5rem (24px)
  - `--font-size-3xl`: 1.875rem (30px)
  - `--font-size-4xl`: 2.25rem (36px)

**Hierarquia de Títulos:**
- **Page Title (H1):** `var(--font-size-2xl)` mobile → `var(--font-size-3xl)` desktop | `font-weight: 700` | `color: var(--color-gray-900)` | `line-height: 1.2`
- **Card Title (H2/H3):** `var(--font-size-lg)` | `font-weight: 600` | `color: var(--color-gray-900)`
- **Section Title:** `var(--font-size-xl)` | `font-weight: 600` | `color: var(--color-gray-900)`
- **Page Description:** `var(--font-size-sm)` mobile → `var(--font-size-base)` desktop | `color: var(--color-gray-600)` | `line-height: 1.5`

**Corpo de Texto:**
- **Padrão:** `var(--font-size-base)` | `line-height: 1.5` | `color: var(--color-gray-900)`
- **Secundário:** `var(--font-size-sm)` | `color: var(--color-gray-600)`
- **Auxiliar:** `var(--font-size-xs)` | `color: var(--color-gray-500)`

### 1.2 Paleta de Cores

**Cores Primárias:**
- `--color-primary`: `#3B82F6` (Azul)
- `--color-primary-hover`: `#2563EB`
- `--color-primary-light`: `#DBEAFE`
- `--color-secondary`: `#6D28D9` (Roxo)
- `--color-secondary-hover`: `#5B21B6`
- `--color-secondary-light`: `#EDE9FE`

**Gradientes Obrigatórios:**
- **Botões Primários:** `linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)`
- **Borda Superior Stat Cards:** `linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%)`
- **Ícones em Background:** `linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)`

**Escala de Cinzas:**
- `--color-gray-50`: `#F9FAFB` (Background)
- `--color-gray-100`: `#F3F4F6` (Hover states)
- `--color-gray-200`: `#E5E7EB` (Bordas)
- `--color-gray-300`: `#D1D5DB` (Bordas inputs)
- `--color-gray-400`: `#9CA3AF` (Placeholders)
- `--color-gray-500`: `#6B7280` (Texto secundário)
- `--color-gray-600`: `#4B5563` (Texto médio)
- `--color-gray-700`: `#374151` (Texto)
- `--color-gray-800`: `#1F2937`
- `--color-gray-900`: `#111827` (Texto principal)

**Cores Semânticas:**
- `--color-success`: `#10B981` | `--color-success-light`: `#D1FAE5`
- `--color-danger`: `#EF4444` | `--color-danger-light`: `#FEE2E2`
- `--color-warning`: `#F59E0B` | `--color-warning-light`: `#FEF3C7`
- `--color-white`: `#FFFFFF`

### 1.3 Botões

**Botão Primário (`.btn-primary`):**
- **Altura:** `48px` (`min-height: 48px`)
- **Padding:** `var(--spacing-2) var(--spacing-4)` (8px 16px)
- **Background:** `var(--color-primary)` (NÃO usar gradiente no background, apenas em hover ou bordas)
- **Cor:** `var(--color-white)`
- **Borda:** `none`
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Fonte:** `var(--font-size-sm)` | `font-weight: 500`
- **Gap entre ícone e texto:** `var(--spacing-2)` (8px)
- **Transição:** `all var(--transition-base)` (200ms ease)
- **Hover:**
  - `background: var(--color-primary-hover)`
  - `transform: translateY(-1px)`
  - `box-shadow: var(--shadow-md)`
- **Ícones:** `20px × 20px` | `stroke-width: 2` | `stroke-linecap: round` | `stroke-linejoin: round`

**Botão Secundário (`.btn-secondary`):**
- **Altura:** `48px`
- **Background:** `var(--color-gray-100)`
- **Cor:** `var(--color-gray-700)`
- **Hover:** `background: var(--color-gray-200)`
- Demais propriedades idênticas ao primário

**Botão Outline (`.btn-outline`):**
- **Background:** `transparent`
- **Borda:** `1px solid var(--color-gray-300)`
- **Cor:** `var(--color-gray-700)`
- **Hover:** `background: var(--color-gray-50)` | `border-color: var(--color-gray-400)`

**Botão Ghost (`.btn-ghost`):**
- **Background:** `transparent`
- **Cor:** `var(--color-gray-700)`
- **Hover:** `background: var(--color-gray-100)`

### 1.4 Cards

**Card Padrão (`.card`):**
- **Background:** `var(--color-white)`
- **Border-radius:** `var(--border-radius-lg)` (12px)
- **Borda:** `1px solid var(--color-gray-200)`
- **Box-shadow:** `var(--shadow-sm)` (0 1px 2px 0 rgba(0, 0, 0, 0.05))
- **Padding:** `var(--spacing-6)` (24px) no `.card-body`
- **Transição:** `all var(--transition-base)`
- **Hover:** `box-shadow: var(--shadow-md)`

**Stat Card (`.stat-card`):**
- **Estrutura:** Idêntica ao `.card`
- **Borda Superior:** `3px` com gradiente `linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%)` via `::before`
- **Padding:** `var(--spacing-6)`
- **Hover:** `transform: translateY(-2px)` | `box-shadow: var(--shadow-lg)`
- **Header:** `.stat-card-header` com `display: flex` | `justify-content: space-between` | `margin-bottom: var(--spacing-4)`
- **Ícone:** `.stat-card-icon` | `40px × 40px` | `background: var(--color-primary-light)` | `color: var(--color-primary)` | `border-radius: var(--border-radius-md)`
- **Valor:** `.stat-card-value` | `var(--font-size-3xl)` | `font-weight: 700` | `line-height: 1`
- **Descrição:** `.stat-card-change` | `var(--font-size-xs)` | `color: var(--color-gray-500)`

### 1.5 Inputs e Formulários

**Input/Select/Textarea (`.form-input`, `.form-select`, `.form-textarea`):**
- **Altura:** `45px` (`padding: var(--spacing-3) var(--spacing-4)` = 12px 16px)
- **Largura:** `100%`
- **Background:** `var(--color-white)`
- **Borda:** `1px solid var(--color-gray-300)`
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Fonte:** `var(--font-size-sm)` | `color: var(--color-gray-900)`
- **Transição:** `all var(--transition-base)`
- **Focus:**
  - `outline: none`
  - `border-color: var(--color-primary)`
  - `box-shadow: 0 0 0 3px var(--color-primary-light)`
- **Placeholder:** `color: var(--color-gray-400)`

**Label (`.form-label`):**
- **Display:** `block`
- **Fonte:** `var(--font-size-sm)` | `font-weight: 500` | `color: var(--color-gray-700)`
- **Margin-bottom:** `var(--spacing-2)` (8px)

**Form Group (`.form-group`):**
- **Margin-bottom:** `var(--spacing-6)` (24px)

**Grid de Formulários:**
- **Desktop:** `display: grid` | `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))` | `gap: var(--spacing-6)`
- **Mobile:** `grid-template-columns: 1fr` (1 coluna)

### 1.6 Ícones

**Padrão SVG:**
- **Tamanho:** `20px × 20px` (padrão) | `16px × 16px` (pequeno) | `24px × 24px` (médio) | `32px × 32px` (grande)
- **ViewBox:** `0 0 24 24`
- **Stroke:** `currentColor`
- **Stroke-width:** `2`
- **Stroke-linecap:** `round`
- **Stroke-linejoin:** `round`
- **Fill:** `none`

**Ícones em Cards:**
- **Background:** `var(--color-primary-light)` ou gradiente
- **Tamanho do container:** `40px × 40px` (stat cards) | `48px × 48px` (cards operacionais)
- **Border-radius:** `var(--border-radius-md)`

### 1.7 Estrutura Geral

**Container Principal:**
- **Max-width:** `1400px` (`.content-wrapper`)
- **Padding:** `var(--spacing-8)` (32px) desktop | `var(--spacing-4)` (16px) mobile
- **Margin:** `0 auto` (centralizado)
- **Width:** `100%`

**Espaçamento Vertical:**
- **Entre seções:** `var(--spacing-8)` (32px)
- **Entre cards:** `var(--spacing-6)` (24px)
- **Entre elementos:** `var(--spacing-4)` (16px)
- **Entre inputs:** `var(--spacing-6)` (24px)

**Grid System:**
- **Stats Grid:** `display: grid` | `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))` | `gap: var(--spacing-6)`
- **Cards Grid:** `display: grid` | `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))` | `gap: var(--spacing-4)`
- **Mobile:** Todos os grids viram `1fr` (1 coluna)

---

## 🔷 2. DETALHAMENTO TELA POR TELA

### 📌 2.1 — Administração → Visão Geral

**Estrutura:**
```
<div class="page-header">
  <h1 class="page-title">Painel Administrativo</h1>
  <p class="page-description">Resumo financeiro e operacional</p>
</div>

<section>
  <h2>Resumo do Campeonato</h2>
  <div class="stats-grid">
    <!-- 4 stat-cards -->
  </div>
</section>

<section>
  <h2>Controle Financeiro</h2>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--spacing-4);">
    <!-- 8 cards financeiros -->
  </div>
</section>

<section>
  <h2>Gestão Operacional</h2>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--spacing-4);">
    <!-- 7 cards operacionais -->
  </div>
</section>
```

**Grid de Resumo do Campeonato:**
- **Layout:** `.stats-grid` (4 cards por linha em desktop, 1 coluna em mobile)
- **Cards:** `.stat-card` com ícone, valor grande e descrição
- **Ícones:** 20px × 20px dentro de container 40px × 40px com `background: var(--color-primary-light)`

**Grid de Controle Financeiro:**
- **Layout:** Grid responsivo `repeat(auto-fit, minmax(220px, 1fr))`
- **Cards:** `.card` simples (não stat-card)
- **Estrutura interna:**
  - Título: `var(--font-size-xs)` | `text-transform: uppercase` | `letter-spacing: 0.08em` | `color: var(--color-gray-500)`
  - Valor: `var(--font-size-2xl)` | `font-weight: 700` | `color: var(--color-gray-900)`
- **8 cards:** Despesas registradas, Despesas pagas, Despesas pendentes, Total gasto, Patrocínios, Entradas extras, Bônus de professores, Lucro/prejuízo

**Grid de Gestão Operacional:**
- **Layout:** Grid `repeat(auto-fit, minmax(240px, 1fr))`
- **Cards:** Usar `partials_operacional_card.html` (componente reutilizável)
- **Estrutura:**
  - Ícone com gradiente em container 48px × 48px
  - Título: `var(--font-size-lg)` | `font-weight: 600`
  - Contagem: `var(--font-size-2xl)` | `font-weight: 700`
  - Botão "Gerenciar": `.btn-secondary` | `width: 100%`

**Títulos de Seção:**
- **H2:** `var(--font-size-xl)` | `font-weight: 600` | `margin-bottom: var(--spacing-4)`
- **Alinhamento:** Esquerda (padrão SHIAI)

**Espaçamento:**
- **Margin-bottom entre seções:** `var(--spacing-8)`
- **Gap entre cards:** `var(--spacing-4)` ou `var(--spacing-6)` conforme o grid

### 📌 2.2 — Administração → Financeiro

**Estrutura:**
```
<div class="page-header">
  <h1 class="page-title">Financeiro</h1>
  <p class="page-description">Entradas e despesas do evento</p>
</div>

<section class="card">
  <h2>Resumo Financeiro</h2>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-4);">
    <!-- Cards de resumo -->
  </div>
</section>

<section class="card">
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <h2 class="card-title">Despesas Recentes</h2>
    <a href="..." class="btn btn-secondary">Gerenciar Despesas</a>
  </div>
  <!-- Lista de despesas -->
</section>
```

**Card de Resumo Financeiro:**
- **Container:** `.card` com `padding: var(--spacing-6)`
- **Grid interno:** `repeat(auto-fit, minmax(200px, 1fr))`
- **Cards internos:** Sem borda, apenas padding
- **Estrutura:**
  - Label: `var(--font-size-xs)` | `text-transform: uppercase` | `color: var(--color-gray-500)`
  - Valor: `var(--font-size-3xl)` | `font-weight: 700` | `color: var(--color-gray-900)`

**Card de Despesas Recentes:**
- **Header:** Flex com título e botão "Gerenciar Despesas"
- **Botão:** `.btn-secondary` | `width: auto` (não 100%)
- **Lista:** Cada despesa em card interno com:
  - Borda: `1px solid var(--color-gray-100)`
  - Border-radius: `var(--border-radius-lg)`
  - Padding: `var(--spacing-3)`
  - Grid interno para nome, categoria, valor, status

**Botão "Gerenciar Despesas":**
- **Estilo:** `.btn-secondary`
- **Posicionamento:** Alinhado à direita no header do card
- **Ícone:** Opcional (ícone de engrenagem ou lista)

### 📌 2.3 — Administração → Equipe Técnica

**Estrutura:**
```
<div class="page-header">
  <h1 class="page-title">Equipe Técnica</h1>
  <p class="page-description">Gestão de árbitros, mesários e coordenadores</p>
</div>

<section>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: var(--spacing-4);">
    <!-- 5 cards usando partials_operacional_card.html -->
  </div>
</section>
```

**Cards:**
- **Componente:** `partials_operacional_card.html`
- **Layout:** Grid 3×2 em desktop (5 cards ocupam 2 linhas)
- **Estrutura do card:**
  - Container: `.card` com `height: 100%` | `display: flex` | `flex-direction: column` | `gap: var(--spacing-4)`
  - Header: Flex com ícone (48px × 48px com gradiente) e título
  - Valor grande: `var(--font-size-2xl)` | `font-weight: 700`
  - Botão "Gerenciar": `.btn-secondary` | `width: 100%` | `justify-content: center`

**Ícones:**
- **Árbitros:** `M12 2l4 4h-3v6h-2V6H8l4-4z` (bandeira)
- **Mesários:** `M4 6h16M4 10h16M4 14h16M4 18h16` (linhas)
- **Oficiais de mesa:** `M5 4h14l1 4H4l1-4zm0 6h14v8H5v-8z` (mesa)
- **Oficiais de pesagem:** `M6 3h12v4H6z M4 9h16v10H4z` (balança)
- **Coordenadores:** `M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2` + `M9 7a4 4 0 1 1 8 0 4 4 0 0 1-8 0` (pessoa)

**Alinhamento:**
- **Vertical:** `align-items: center` no header
- **Horizontal:** `justify-content: space-between` no header
- **Gap:** `var(--spacing-3)` entre ícone e texto

### 📌 2.4 — Administração → Cadastros Operacionais

**Estrutura:**
```
<div class="page-header">
  <div style="display: flex; align-items: center; gap: var(--spacing-3);">
    <div style="width: 48px; height: 48px; ...gradiente...">
      <svg>...</svg>
    </div>
    <div>
      <h1 class="page-title">{{ tipo_display }}</h1>
      <p class="page-description">Gerencie {{ tipo_display|lower }}</p>
    </div>
  </div>
</div>

<section class="card">
  <div class="card-header">
    <h3 class="card-title">Cadastrar {{ tipo_display }}</h3>
  </div>
  <div class="card-body">
    <form style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-6);">
      <!-- Inputs -->
    </form>
  </div>
</section>

<section class="card">
  <div class="card-header">
    <h3 class="card-title">Registros</h3>
  </div>
  <div class="card-body">
    <!-- Lista de registros -->
  </div>
</section>
```

**Formulário:**
- **Container:** `.card` com `.card-header` e `.card-body`
- **Grid:** `repeat(auto-fit, minmax(300px, 1fr))` | `gap: var(--spacing-6)`
- **Inputs:**
  - Altura: `45px`
  - Classe: `.form-input` ou `.form-select`
  - Labels: `.form-label`
  - Form-group: `.form-group` com `margin-bottom: var(--spacing-6)`
- **Botão "Adicionar":**
  - `.btn-primary`
  - Altura: `48px`
  - Grid-column: `1 / -1` (largura total)
  - Margin-top: `var(--spacing-6)`

**Card de Registros:**
- **Container:** `.card` separado
- **Header:** `.card-header` com `.card-title`
- **Body:** `.card-body` com lista
- **Cada registro:**
  - Card interno com `border: 1px solid var(--color-gray-100)` | `border-radius: var(--border-radius-lg)` | `padding: var(--spacing-3)`
  - Grid interno para campos editáveis
  - Botões: "Atualizar" (`.btn-primary`) e "Excluir" (`.btn-outline` com cor danger)

**Título:**
- **Ícone:** 48px × 48px com gradiente no header da página
- **Alinhamento:** Esquerda (padrão SHIAI)

### 📌 2.5 — Administração → Relatórios Administrativos

**Estrutura:**
```
<div class="page-header">
  <h1 class="page-title">Relatórios Administrativos</h1>
  <p class="page-description">Gere relatórios em PDF e CSV</p>
</div>

<section>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--spacing-6);">
    <!-- Cards de relatórios -->
  </div>
</section>
```

**Cards de Relatórios:**
- **Layout:** Grid `repeat(auto-fit, minmax(280px, 1fr))` | `gap: var(--spacing-6)`
- **Estrutura do card:**
  - Container: `.card` com `padding: var(--spacing-6)`
  - Ícone: 48px × 48px com gradiente (mesmo padrão dos outros cards)
  - Título: `var(--font-size-lg)` | `font-weight: 600`
  - Descrição: `var(--font-size-sm)` | `color: var(--color-gray-600)`
  - Botão "Gerar": `.btn-primary` | `width: 100%` | `margin-top: var(--spacing-4)`

**Ícones:**
- **PDF Financeiro:** `M4 4h16v16H4z` (documento)
- **PDF Equipe:** `M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2` (pessoas)
- **PDF Estrutura:** `M4 6h16v4H4z M4 12h16v6H4z` (estrutura)
- **PDF Patrocínios:** `M12 2l3 7h7l-5.5 4 2.5 7-7-4-7 4 2.5-7L2 9h7z` (estrela)
- **CSV:** `M4 4h16v16H4z` + `M9 4v16M4 9h16` (tabela)

**Hover e Estados:**
- **Card hover:** `box-shadow: var(--shadow-md)` | `transform: translateY(-2px)`
- **Botão hover:** `background: var(--color-primary-hover)` | `transform: translateY(-1px)`

**Espaçamento:**
- **Superior:** `var(--spacing-8)` após page-header
- **Inferior:** `var(--spacing-8)` antes do footer (se houver)

---

## 🔷 3. SIDEBAR — SUBMENU ADMINISTRATIVO

**Estrutura:**
```html
<div class="nav-section">
  <div class="nav-section-title">ADMINISTRAÇÃO</div>
  <a href="..." class="nav-item {% if ... %}active{% endif %}">
    <svg class="nav-icon">...</svg>
    <span>Visão Geral</span>
  </a>
  <!-- Outros itens -->
</div>
```

**Estilo do Título da Seção:**
- **Classe:** `.nav-section-title`
- **Fonte:** `var(--font-size-xs)` (12px)
- **Font-weight:** `600`
- **Cor:** `var(--color-gray-500)`
- **Text-transform:** `uppercase`
- **Letter-spacing:** `0.05em`
- **Padding:** `0 var(--spacing-3) var(--spacing-2)`
- **Margin-bottom:** `var(--spacing-2)`

**Estilo dos Itens:**
- **Classe:** `.nav-item`
- **Display:** `flex`
- **Align-items:** `center`
- **Gap:** `var(--spacing-3)` (12px)
- **Padding:** `var(--spacing-2) var(--spacing-3)` (8px 12px)
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Fonte:** `var(--font-size-sm)` | `font-weight: 500`
- **Cor:** `var(--color-gray-700)`
- **Transição:** `all var(--transition-base)`
- **Margin-bottom:** `var(--spacing-1)` (4px)

**Estados:**
- **Hover:** `background: var(--color-gray-100)` | `color: var(--color-gray-900)`
- **Active:** `background: var(--color-primary-light)` | `color: var(--color-primary)` + `::before` com barra lateral `3px` | `height: 60%` | `background: var(--color-primary)`

**Ícones:**
- **Tamanho:** `20px × 20px`
- **Classe:** `.nav-icon`
- **Stroke-width:** `2`
- **Ícones específicos:**
  - Visão Geral: `M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z` (checkmark)
  - Financeiro: `M4 6h16M4 10h16M4 14h16M4 18h16` (linhas/documento)
  - Equipe Técnica: `M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2` + `M9 7a4 4 0 1 1 8 0 4 4 0 0 1-8 0` (pessoas)
  - Cadastros Operacionais: `M4 4h16v16H4z` + `M9 4v16` + `M4 9h16` (tabela)
  - Insumos: `M4 6h16v4H4z M4 12h16v6H4z` (caixas)
  - Patrocínios: `M12 2l3 7h7l-5.5 4 2.5 7-7-4-7 4 2.5-7L2 9h7z` (estrela)
  - Relatórios: `M4 4h16v16H4z` + `M9 4v16` + `M4 9h16` (documento/tabela)

**Espaçamento entre Seções:**
- **Margin-bottom da seção:** `var(--spacing-6)` (24px)
- **Distância visual:** Suficiente para separar "Global", "Evento Ativo" e "Administração"

**Comportamento Accordion:**
- **Não há accordion** — todas as seções sempre visíveis
- **Scroll:** Sidebar com `overflow-y: auto` se necessário

**Responsividade Mobile:**
- **Sidebar:** `transform: translateX(-100%)` por padrão
- **Toggle:** Botão hambúrguer no navbar
- **Overlay:** `.sidebar-overlay` com `background: rgba(0, 0, 0, 0.5)` quando sidebar aberta
- **Itens:** Mesmo estilo, mas com padding maior para touch

---

## 🔷 4. ESTILIZAÇÃO DE IMPRESSÃO

**Media Query:**
```css
@media print {
  /* Estilos exclusivos para impressão */
}
```

**Layout A4:**
- **@page:**
  - `size: A4 portrait`
  - `margin: 12mm` (mínimo 10-15mm)
- **Body:**
  - `width: 190mm` (A4 menos margens)
  - `font-size: 9pt`
  - `line-height: 1.3`
  - `color: #000`
  - `background: #fff`

**Cabeçalho:**
- **Container:** `.print-header`
- **Border-bottom:** `2px solid #000`
- **Padding-bottom:** `4mm`
- **Margin-bottom:** `6mm`
- **Título (H1):**
  - `font-size: 14pt`
  - `font-weight: bold`
  - `text-transform: uppercase`
- **Info Grid:** `grid-template-columns: 1fr 1fr` | `gap: 2mm` | `font-size: 8pt`

**Estrutura das Chaves:**
- **Container:** `.print-container` | `display: flex` | `flex-direction: column` | `gap: 4mm`
- **Round Section:** `.round-section` | `margin-bottom: 5mm` | `page-break-inside: avoid`
- **Round Title:** `font-size: 10pt` | `font-weight: bold` | `text-transform: uppercase` | `border-bottom: 1px solid #000` | `padding-bottom: 1mm`

**Luta Card (Print):**
- **Container:** `.luta-print`
- **Grid:** `grid-template-columns: 1fr auto 1fr` | `gap: 3mm`
- **Borda:** `1px solid #000`
- **Padding:** `3mm`
- **Min-height:** `25mm`
- **Page-break:** `page-break-inside: avoid`

**Fighter Box:**
- **Borda:** `1px solid #333`
- **Padding:** `2mm`
- **Min-height:** `20mm`
- **Azul:** `background: #f0f0f0` | `border-left: 3px solid #000`
- **Branco:** `background: #fff` | `border-right: 3px solid #000`

**Campos para Anotações:**
- **Container:** `.annotation-fields`
- **Border-top:** `1px dotted #666`
- **Font-size:** `7pt`
- **Linhas:** `.annotation-line` com `border-bottom: 1px solid #000` | `min-height: 4mm`

**Seta de Avanço:**
- **Container:** `.arrow-container` | `text-align: center` | `margin: 2mm 0`
- **Seta:** `.arrow-down` (triângulo CSS) | `border-top: 8px solid #000`
- **Linha:** `.arrow-line` | `width: 1px` | `height: 8mm` | `background: #000`

**Colocações:**
- **Container:** `.colocacoes-box`
- **Borda:** `2px solid #000`
- **Padding:** `3mm`
- **Margin-top:** `5mm`
- **Grid:** `grid-template-columns: repeat(4, 1fr)` | `gap: 2mm`

**Remoção de Elementos:**
- **Ocultar:** Sidebar, navbar, botões, menus, elementos responsivos
- **CSS:** `display: none !important` para `.sidebar`, `.navbar`, `.btn`, etc.

**Cabeçalho Padrão SHIAI:**
- **Logo:** Opcional (se houver)
- **Título do Evento:** `font-size: 14pt` | `font-weight: bold`
- **Informações:** Categoria, Classe, Sexo, Peso em grid 2 colunas

**Paginação:**
- **Page-break:** `page-break-after: auto` no container principal
- **Evitar quebras:** `page-break-inside: avoid` em cards de luta

---

## 🔷 5. RESPONSIVIDADE (MOBILE-FIRST)

### 5.1 Breakpoints

**Mobile First Base (< 480px):**
- Todos os grids: `grid-template-columns: 1fr`
- Padding: `var(--spacing-4)` (16px)
- Font-size: Reduzido em títulos (H1: `var(--font-size-2xl)`)

**Tablet (≥ 768px):**
- Grids: `repeat(auto-fit, minmax(240px, 1fr))`
- Padding: `var(--spacing-6)`
- Font-size: Padrão

**Desktop (≥ 1024px):**
- Grids: `repeat(auto-fit, minmax(280px, 1fr))` ou mais colunas
- Padding: `var(--spacing-8)`
- Font-size: Aumentado (H1: `var(--font-size-3xl)`)

### 5.2 Adaptação de Cards

**Mobile:**
- **Stats Grid:** `flex-direction: column` | `gap: var(--spacing-4)`
- **Cards:** Largura 100%, sem grid
- **Card interno:** Padding reduzido se necessário

**Desktop:**
- **Stats Grid:** `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))`
- **Cards:** Grid responsivo

### 5.3 Inputs

**Mobile:**
- **Largura:** `100%` (sempre)
- **Altura:** `45px` (mantida)
- **Grid:** `grid-template-columns: 1fr` (1 coluna)

**Desktop:**
- **Grid:** `repeat(auto-fit, minmax(300px, 1fr))` (múltiplas colunas)

### 5.4 Navegação Mobile

**Sidebar:**
- **Estado padrão:** `transform: translateX(-100%)` (oculta)
- **Estado ativo:** `transform: translateX(0)` (visível)
- **Overlay:** `.sidebar-overlay` com `display: block` quando ativa
- **Z-index:** `1000` (sidebar) | `999` (overlay)

**Hamburger Menu:**
- **Botão:** `.btn-ghost` no navbar
- **Ícone:** `20px × 20px`
- **Display:** `block` em mobile | `none` em desktop (≥ 1024px)

### 5.5 Reorganização de Grids

**Mobile:**
- Todos os grids viram `1fr` (1 coluna)
- Cards empilhados verticalmente
- Gap reduzido: `var(--spacing-4)` ao invés de `var(--spacing-6)`

**Desktop:**
- Grids com múltiplas colunas
- Gap padrão: `var(--spacing-6)`

**Exemplo de Media Query:**
```css
@media (max-width: 767px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-4);
  }
}

@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: var(--spacing-6);
  }
}
```

---

## 🔷 6. DOCUMENTO FINAL DE REFERÊNCIA

### 6.1 Padrões de UI

**Componentes Reutilizáveis:**
1. **`.card`** — Card padrão com hover
2. **`.stat-card`** — Card de estatística com gradiente superior
3. **`.btn-primary`** — Botão primário (48px)
4. **`.btn-secondary`** — Botão secundário (48px)
5. **`.form-input`** — Input padrão (45px)
6. **`.form-select`** — Select padrão (45px)
7. **`.form-label`** — Label padrão
8. **`.page-header`** — Cabeçalho de página
9. **`.stats-grid`** — Grid de estatísticas
10. **`partials_operacional_card.html`** — Card operacional reutilizável

### 6.2 Tamanhos Exatos

| Elemento | Altura | Largura | Padding | Border-radius |
|----------|--------|---------|---------|---------------|
| Botão Primário | 48px | auto | 8px 16px | 8px |
| Input/Select | 45px | 100% | 12px 16px | 8px |
| Card | auto | 100% | 24px | 12px |
| Stat Card | auto | min 240px | 24px | 12px |
| Ícone Nav | 20px | 20px | - | - |
| Ícone Card | 20px | 20px | - | - |
| Container Ícone | 40px | 40px | - | 8px |

### 6.3 Regras de Grid

**Stats Grid:**
- `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))`
- `gap: var(--spacing-6)`
- Mobile: `1fr`

**Cards Grid:**
- `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))`
- `gap: var(--spacing-4)`
- Mobile: `1fr`

**Form Grid:**
- `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`
- `gap: var(--spacing-6)`
- Mobile: `1fr`

### 6.4 Tabela de Cores

| Uso | Variável | Valor Hex | Aplicação |
|-----|----------|-----------|-----------|
| Primário | `--color-primary` | `#3B82F6` | Botões, links, ícones |
| Secundário | `--color-secondary` | `#6D28D9` | Gradientes, acentos |
| Sucesso | `--color-success` | `#10B981` | Badges, confirmações |
| Perigo | `--color-danger` | `#EF4444` | Erros, exclusões |
| Aviso | `--color-warning` | `#F59E0B` | Alertas, pendências |
| Texto Principal | `--color-gray-900` | `#111827` | Títulos, texto |
| Texto Secundário | `--color-gray-600` | `#4B5563` | Descrições |
| Texto Auxiliar | `--color-gray-500` | `#6B7280` | Labels, hints |
| Borda | `--color-gray-200` | `#E5E7EB` | Cards, inputs |
| Background | `--color-gray-50` | `#F9FAFB` | Body, cards footer |

### 6.5 Tabela de Tipografia

| Elemento | Tamanho | Peso | Cor | Line-height |
|----------|---------|------|-----|-------------|
| Page Title (Mobile) | 24px | 700 | gray-900 | 1.2 |
| Page Title (Desktop) | 30px | 700 | gray-900 | 1.2 |
| Card Title | 18px | 600 | gray-900 | 1.3 |
| Section Title | 20px | 600 | gray-900 | 1.3 |
| Body Text | 16px | 400 | gray-900 | 1.5 |
| Small Text | 14px | 400 | gray-600 | 1.5 |
| Label | 14px | 500 | gray-700 | 1.4 |
| Stat Value | 30px | 700 | gray-900 | 1.0 |
| Stat Description | 12px | 400 | gray-500 | 1.4 |

### 6.6 Comportamentos de Interação

**Hover:**
- **Cards:** `box-shadow: var(--shadow-md)` | `transform: translateY(-2px)` (stat-cards)
- **Botões:** `background: var(--color-primary-hover)` | `transform: translateY(-1px)` | `box-shadow: var(--shadow-md)`
- **Nav Items:** `background: var(--color-gray-100)` | `color: var(--color-gray-900)`
- **Inputs:** `border-color: var(--color-primary)` (via focus)

**Focus:**
- **Inputs:** `outline: none` | `border-color: var(--color-primary)` | `box-shadow: 0 0 0 3px var(--color-primary-light)`
- **Botões:** Mesmo estilo de hover

**Active:**
- **Nav Items:** `background: var(--color-primary-light)` | `color: var(--color-primary)` + barra lateral
- **Botões:** `transform: translateY(0)` (sem elevação)

**Transições:**
- **Padrão:** `all var(--transition-base)` (200ms ease)
- **Rápida:** `all var(--transition-fast)` (150ms ease)
- **Lenta:** `all var(--transition-slow)` (300ms ease)

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Base e Componentes
- [ ] Garantir que todas as CSS variables estão definidas
- [ ] Criar/verificar componentes reutilizáveis
- [ ] Padronizar `.card`, `.stat-card`, `.btn-*`, `.form-*`

### Fase 2: Sidebar
- [ ] Criar submenu ADMINISTRAÇÃO na sidebar
- [ ] Adicionar ícones corretos
- [ ] Implementar estados active/hover
- [ ] Testar responsividade mobile

### Fase 3: Telas Administrativas
- [ ] Visão Geral (painel.html)
- [ ] Financeiro (financeiro.html)
- [ ] Equipe Técnica (equipe.html)
- [ ] Cadastros Operacionais (cadastros_operacionais.html)
- [ ] Insumos (insumos.html)
- [ ] Patrocínios (patrocinios.html)
- [ ] Relatórios (relatorios.html)

### Fase 4: Formulários
- [ ] Padronizar todos os inputs (45px)
- [ ] Aplicar grid responsivo
- [ ] Adicionar labels corretos
- [ ] Estilizar botões de ação

### Fase 5: Impressão
- [ ] Criar layout A4 para chaves
- [ ] Remover elementos desnecessários
- [ ] Testar em diferentes navegadores
- [ ] Verificar paginação

### Fase 6: Responsividade
- [ ] Testar mobile (< 480px)
- [ ] Testar tablet (768px - 1023px)
- [ ] Testar desktop (≥ 1024px)
- [ ] Verificar sidebar mobile
- [ ] Validar grids em todas as telas

### Fase 7: Validação Final
- [ ] Comparar visualmente com outras telas do sistema
- [ ] Verificar consistência de cores, espaçamentos, tipografia
- [ ] Testar interações (hover, focus, active)
- [ ] Validar acessibilidade básica

---

**Documento criado em:** {{ data_atual }}  
**Versão:** 1.0  
**Status:** Aguardando aprovação para implementação

