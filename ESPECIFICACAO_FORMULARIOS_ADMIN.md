# 📋 ESPECIFICAÇÃO COMPLETA DE FORMULÁRIOS
## Módulo Administrativo SHIAI SISTEM

**Documento Complementar à:** `ESPECIFICACAO_ESTILIZACAO_ADMIN.md`

---

## 🔷 1. PADRONIZAÇÃO GLOBAL DOS FORMULÁRIOS (OBRIGATÓRIA)

### 1.1 Estrutura Base de Todo Formulário

**Template Obrigatório:**
```html
<div class="page-header">
    <h1 class="page-title">Título do Formulário</h1>
    <p class="page-description">Descrição do formulário</p>
</div>

<div class="card">
    <div class="card-header">
        <h3 class="card-title">Seção do Formulário</h3>
    </div>
    <div class="card-body">
        <form method="post" enctype="multipart/form-data">
            {% csrf_token %}
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-6);">
                <!-- Campos do formulário -->
            </div>
            <div style="display: flex; gap: var(--spacing-3); justify-content: flex-end; margin-top: var(--spacing-8); padding-top: var(--spacing-6); border-top: 1px solid var(--color-gray-200);">
                <a href="..." class="btn btn-secondary">Cancelar</a>
                <button type="submit" class="btn btn-primary">
                    <svg>...</svg>
                    Salvar
                </button>
            </div>
        </form>
    </div>
</div>
```

### 1.2 Inputs (Campos de Texto)

**Especificações Técnicas:**
- **Classe:** `.form-input`
- **Altura:** `45px` (via `padding: var(--spacing-3) var(--spacing-4)` = 12px 16px)
- **Largura:** `100%`
- **Background:** `var(--color-white)`
- **Borda:** `1px solid var(--color-gray-300)` (`#E5E7EB`)
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Fonte:** `var(--font-size-sm)` (14px) | `font-weight: 400` | `color: var(--color-gray-900)`
- **Padding:** `12px 16px`
- **Box-shadow:** `var(--shadow-sm)` (0 1px 2px 0 rgba(0, 0, 0, 0.05))
- **Transição:** `all var(--transition-base)` (200ms ease)

**Estado Focus:**
```css
.form-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px var(--color-primary-light);
}
```

**Placeholder:**
- **Cor:** `var(--color-gray-400)` (`#9CA3AF`)
- **Estilo:** Normal (não itálico)

**Exemplo HTML:**
```html
<div class="form-group">
    <label class="form-label" for="nome">
        Nome completo
        <span style="color: var(--color-danger);">*</span>
    </label>
    <input type="text" id="nome" name="nome" class="form-input" required placeholder="Digite o nome">
</div>
```

### 1.3 Selects (Campos de Seleção)

**Especificações Técnicas:**
- **Classe:** `.form-select`
- **Altura:** `45px` (idêntico aos inputs)
- **Largura:** `100%`
- **Background:** `var(--color-white)`
- **Borda:** `1px solid var(--color-gray-300)`
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Padding:** `12px 16px`
- **Aparência:** `appearance: none` (remover seta padrão)
- **Background-image:** Seta customizada SVG (opcional, mas recomendado)

**Exemplo HTML:**
```html
<div class="form-group">
    <label class="form-label" for="categoria">Categoria</label>
    <select id="categoria" name="categoria" class="form-select" required>
        <option value="">Selecione</option>
        <option value="1">Opção 1</option>
    </select>
</div>
```

**Seta Customizada (CSS):**
```css
.form-select {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%234B5563' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    padding-right: 40px;
}
```

### 1.4 Textareas (Áreas de Texto)

**Especificações Técnicas:**
- **Classe:** `.form-input` ou `.form-textarea`
- **Altura mínima:** `120px` (`min-height: 120px`)
- **Largura:** `100%`
- **Resize:** `vertical` (permitir redimensionar apenas verticalmente)
- **Padding:** `12px 16px`
- **Borda:** `1px solid var(--color-gray-300)`
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Fonte:** `var(--font-size-sm)` (14px)
- **Line-height:** `1.5`

**Exemplo HTML:**
```html
<div class="form-group" style="grid-column: 1 / -1;">
    <label class="form-label" for="observacao">Observação</label>
    <textarea id="observacao" name="observacao" class="form-input" placeholder="Notas adicionais" rows="4"></textarea>
</div>
```

### 1.5 Labels

**Especificações Técnicas:**
- **Classe:** `.form-label`
- **Display:** `block`
- **Fonte:** `var(--font-size-sm)` (14px)
- **Font-weight:** `500` (medium)
- **Cor:** `var(--color-gray-700)` (`#374151`)
- **Margin-bottom:** `var(--spacing-2)` (8px)
- **Alinhamento:** Esquerda (padrão)

**Campos Obrigatórios:**
- Adicionar asterisco vermelho: `<span style="color: var(--color-danger);">*</span>`

**Exemplo HTML:**
```html
<label class="form-label" for="nome">
    Nome completo
    <span style="color: var(--color-danger);">*</span>
</label>
```

### 1.6 Form Groups

**Especificações Técnicas:**
- **Classe:** `.form-group`
- **Margin-bottom:** `var(--spacing-6)` (24px)
- **Display:** `block` (padrão)

**Em Grids:**
- Quando dentro de grid, `margin-bottom: 0` (o gap do grid cuida do espaçamento)

**Exemplo HTML:**
```html
<div class="form-group" style="margin-bottom: 0;">
    <label class="form-label" for="nome">Nome</label>
    <input type="text" id="nome" name="nome" class="form-input">
</div>
```

### 1.7 Grid de Formulários

**Desktop (≥ 768px):**
```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
gap: var(--spacing-6); /* 24px */
```

**Mobile (< 768px):**
```css
display: grid;
grid-template-columns: 1fr; /* 1 coluna */
gap: var(--spacing-6);
```

**Campos de Largura Total:**
- Usar `style="grid-column: 1 / -1;"` para campos que devem ocupar toda a largura (textareas, file inputs, checkboxes)

**Exemplo HTML:**
```html
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-6);">
    <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label" for="nome">Nome</label>
        <input type="text" id="nome" name="nome" class="form-input">
    </div>
    <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label" for="telefone">Telefone</label>
        <input type="text" id="telefone" name="telefone" class="form-input">
    </div>
    <div class="form-group" style="grid-column: 1 / -1; margin-bottom: 0;">
        <label class="form-label" for="observacao">Observação</label>
        <textarea id="observacao" name="observacao" class="form-input" rows="4"></textarea>
    </div>
</div>
```

### 1.8 Cards de Formulário

**Estrutura Obrigatória:**
```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Título da Seção</h3>
    </div>
    <div class="card-body">
        <!-- Formulário aqui -->
    </div>
</div>
```

**Especificações:**
- **Background:** `var(--color-white)`
- **Border-radius:** `var(--border-radius-lg)` (12px)
- **Borda:** `1px solid var(--color-gray-200)`
- **Box-shadow:** `var(--shadow-sm)`
- **Padding do body:** `var(--spacing-6)` (24px)
- **Padding do header:** `var(--spacing-6)` (24px)
- **Border-bottom do header:** `1px solid var(--color-gray-200)`

### 1.9 Botões de Formulário

**Botão Primário (Salvar/Adicionar):**
```html
<button type="submit" class="btn btn-primary">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
        <polyline points="17 21 17 13 7 13 7 21"></polyline>
        <polyline points="7 3 7 8 15 8"></polyline>
    </svg>
    Salvar
</button>
```

**Botão Secundário (Cancelar):**
```html
<a href="..." class="btn btn-secondary">Cancelar</a>
```

**Container de Botões:**
```html
<div style="display: flex; gap: var(--spacing-3); justify-content: flex-end; margin-top: var(--spacing-8); padding-top: var(--spacing-6); border-top: 1px solid var(--color-gray-200);">
    <a href="..." class="btn btn-secondary">Cancelar</a>
    <button type="submit" class="btn btn-primary">Salvar</button>
</div>
```

**Especificações dos Botões:**
- **Altura:** `48px` (`min-height: 48px`)
- **Padding:** `var(--spacing-2) var(--spacing-4)` (8px 16px)
- **Border-radius:** `var(--border-radius-md)` (8px)
- **Gap entre ícone e texto:** `var(--spacing-2)` (8px)
- **Fonte:** `var(--font-size-sm)` (14px) | `font-weight: 500`

---

## 🔷 2. DETALHAMENTO FORMULÁRIO POR FORMULÁRIO

### 📌 2.1 — Formulário de Cadastros Operacionais

**Arquivo:** `atletas/templates/atletas/administracao/cadastros_operacionais.html`

**Campos:**
1. **Nome** (obrigatório)
2. **Telefone / WhatsApp** (opcional)
3. **Observação** (opcional, textarea)

**Estrutura Atual vs. Estrutura Corrigida:**

**❌ ESTRUTURA ATUAL (INCORRETA):**
```html
<section class="card">
    <h1 style="margin:0 0 var(--spacing-4) 0;">{{ tipo_display }}</h1>
    <form method="post" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--spacing-3);">
        <!-- Campos sem card-header/card-body -->
    </form>
</section>
```

**✅ ESTRUTURA CORRIGIDA:**
```html
<div class="page-header">
    <div style="display: flex; align-items: center; gap: var(--spacing-3);">
        <div style="width: 48px; height: 48px; border-radius: var(--border-radius-md); background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%); display: flex; align-items: center; justify-content: center;">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px;">
                <!-- Ícone específico do tipo -->
            </svg>
        </div>
        <div>
            <h1 class="page-title">{{ tipo_display }}</h1>
            <p class="page-description">Gerencie {{ tipo_display|lower }}</p>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h3 class="card-title">Cadastrar {{ tipo_display }}</h3>
    </div>
    <div class="card-body">
        <form method="post">
            {% csrf_token %}
            <input type="hidden" name="criar" value="1">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-6);">
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="nome">
                        Nome
                        <span style="color: var(--color-danger);">*</span>
                    </label>
                    <input type="text" id="nome" name="nome" class="form-input" required placeholder="Nome completo">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="telefone">Telefone / WhatsApp</label>
                    <input type="text" id="telefone" name="telefone" class="form-input" placeholder="(99) 99999-9999">
                </div>
                <div class="form-group" style="grid-column: 1 / -1; margin-bottom: 0;">
                    <label class="form-label" for="observacao">Observação</label>
                    <textarea id="observacao" name="observacao" class="form-input" placeholder="Notas" rows="4"></textarea>
                </div>
            </div>
            <div style="display: flex; gap: var(--spacing-3); justify-content: flex-end; margin-top: var(--spacing-8); padding-top: var(--spacing-6); border-top: 1px solid var(--color-gray-200);">
                <button type="submit" class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19"></line>
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                    </svg>
                    Adicionar
                </button>
            </div>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h3 class="card-title">Registros</h3>
    </div>
    <div class="card-body">
        <!-- Lista de registros -->
    </div>
</div>
```

**Correções Obrigatórias:**
1. ✅ Adicionar `page-header` com ícone e descrição
2. ✅ Envolver formulário em `.card` com `.card-header` e `.card-body`
3. ✅ Alterar grid de `minmax(220px, 1fr)` para `minmax(300px, 1fr)`
4. ✅ Alterar gap de `var(--spacing-3)` para `var(--spacing-6)`
5. ✅ Garantir que inputs tenham altura de 45px
6. ✅ Adicionar asterisco vermelho em campos obrigatórios
7. ✅ Separar card de "Registros" do card de formulário
8. ✅ Botão "Adicionar" com ícone e estilo `.btn-primary`
9. ✅ Container de botões com border-top e espaçamento correto

**Card de Registros:**
```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Registros</h3>
    </div>
    <div class="card-body">
        {% if cadastros %}
            <div style="display: flex; flex-direction: column; gap: var(--spacing-4);">
                {% for cadastro in cadastros %}
                <div class="card" style="padding: var(--spacing-4); border: 1px solid var(--color-gray-100);">
                    <form method="post">
                        {% csrf_token %}
                        <input type="hidden" name="cadastro_id" value="{{ cadastro.id }}">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-4);">
                            <!-- Campos editáveis -->
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: var(--spacing-2); margin-top: var(--spacing-4);">
                            <button type="submit" name="editar" value="1" class="btn btn-primary">Salvar</button>
                            <button type="submit" name="deletar" value="1" class="btn btn-outline" style="color: var(--color-danger); border-color: var(--color-danger);">Remover</button>
                            <!-- Botão WhatsApp se houver telefone -->
                        </div>
                    </form>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <p style="color: var(--color-gray-500); margin: 0;">Nenhum registro para este tipo.</p>
        {% endif %}
    </div>
</div>
```

### 📌 2.2 — Formulário de Despesas

**Arquivo:** `atletas/templates/atletas/administracao/despesas.html`

**Campos:**
1. **Categoria** (obrigatório, select)
2. **Nome** (obrigatório)
3. **Valor** (obrigatório, number com step 0.01)
4. **Status** (select: Pago/Pendente)
5. **Contato Responsável** (opcional)
6. **WhatsApp** (opcional)
7. **Observação** (opcional, textarea)

**Estrutura Corrigida:**
```html
<div class="page-header">
    <h1 class="page-title">Despesas do Evento</h1>
    <p class="page-description">Controle completo das saídas financeiras</p>
</div>

<div class="card">
    <div class="card-header">
        <h3 class="card-title">Cadastrar Despesa</h3>
    </div>
    <div class="card-body">
        <form method="post">
            {% csrf_token %}
            <input type="hidden" name="criar" value="1">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-6);">
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="categoria">
                        Categoria
                        <span style="color: var(--color-danger);">*</span>
                    </label>
                    <select id="categoria" name="categoria" class="form-select" required>
                        <option value="">Selecione</option>
                        {% for value, label in categorias %}
                        <option value="{{ value }}">{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="nome">
                        Nome
                        <span style="color: var(--color-danger);">*</span>
                    </label>
                    <input type="text" id="nome" name="nome" class="form-input" required placeholder="Ex: Árbitro chefe">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="valor">
                        Valor
                        <span style="color: var(--color-danger);">*</span>
                    </label>
                    <input type="number" step="0.01" id="valor" name="valor" class="form-input" required placeholder="0,00">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="status">Status</label>
                    <select id="status" name="status" class="form-select">
                        {% for value, label in status_choices %}
                        <option value="{{ value }}">{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="contato_nome">Contato Responsável</label>
                    <input type="text" id="contato_nome" name="contato_nome" class="form-input" placeholder="Nome do responsável">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="contato_whatsapp">WhatsApp</label>
                    <input type="text" id="contato_whatsapp" name="contato_whatsapp" class="form-input" placeholder="(99) 99999-9999">
                </div>
                <div class="form-group" style="grid-column: 1 / -1; margin-bottom: 0;">
                    <label class="form-label" for="observacao">Observação</label>
                    <textarea id="observacao" name="observacao" class="form-input" placeholder="Notas adicionais" rows="3"></textarea>
                </div>
            </div>
            <div style="display: flex; gap: var(--spacing-3); justify-content: flex-end; margin-top: var(--spacing-8); padding-top: var(--spacing-6); border-top: 1px solid var(--color-gray-200);">
                <button type="submit" class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
                        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                        <polyline points="17 21 17 13 7 13 7 21"></polyline>
                        <polyline points="7 3 7 8 15 8"></polyline>
                    </svg>
                    Salvar Despesa
                </button>
            </div>
        </form>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h3 class="card-title">Despesas Registradas</h3>
    </div>
    <div class="card-body">
        <!-- Lista de despesas -->
    </div>
</div>
```

**Correções Obrigatórias:**
1. ✅ Adicionar `page-header` padronizado
2. ✅ Envolver formulário em `.card` com header/body
3. ✅ Alterar grid para `minmax(300px, 1fr)` e gap `var(--spacing-6)`
4. ✅ Garantir altura de 45px em todos os inputs
5. ✅ Adicionar asteriscos em campos obrigatórios
6. ✅ Campo "Valor" com máscara monetária (JavaScript opcional)
7. ✅ Botão "Salvar Despesa" com ícone e estilo correto

**Máscara Monetária (JavaScript Opcional):**
```javascript
document.getElementById('valor').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = (value / 100).toFixed(2) + '';
    value = value.replace('.', ',');
    value = value.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    e.target.value = value;
});
```

### 📌 2.3 — Formulário de Entradas Extras

**Estrutura:** Idêntica ao formulário de despesas, mas com campos específicos para entradas extras.

**Campos Sugeridos:**
1. **Tipo de Entrada** (select)
2. **Descrição** (text)
3. **Valor** (number)
4. **Data** (date)
5. **Observação** (textarea)

**Aplicar mesmas correções do formulário de despesas.**

### 📌 2.4 — Formulário de Patrocínios

**Campos:**
1. **Nome do Patrocinador** (obrigatório)
2. **Valor do Patrocínio** (obrigatório, number)
3. **Tipo** (select: Financeiro/Material)
4. **Contato** (text)
5. **Telefone/WhatsApp** (text)
6. **Notas** (textarea)

**Estrutura Corrigida:**
```html
<div class="page-header">
    <h1 class="page-title">Patrocínios</h1>
    <p class="page-description">Gerencie patrocinadores do evento</p>
</div>

<div class="card">
    <div class="card-header">
        <h3 class="card-title">Cadastrar Patrocínio</h3>
    </div>
    <div class="card-body">
        <form method="post">
            {% csrf_token %}
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-6);">
                <!-- Campos padronizados -->
            </div>
            <!-- Botões padronizados -->
        </form>
    </div>
</div>
```

**Correções:**
1. ✅ Mesma estrutura de card e grid
2. ✅ Campo "Valor" com formatação monetária
3. ✅ Select "Tipo" padronizado
4. ✅ Card separado para upload de logos (se implementado no futuro)

### 📌 2.5 — Formulário de Ambulância / Insumos / Estrutura

**Estrutura:** Similar aos cadastros operacionais, mas com campos específicos.

**Campos Comuns:**
1. **Nome/Descrição** (obrigatório)
2. **Contato** (opcional)
3. **Telefone** (opcional)
4. **Observação** (textarea)

**Aplicar mesmas correções dos cadastros operacionais.**

### 📌 2.6 — Formulários de Filtro / Busca

**Estrutura Padronizada:**
```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Filtros</h3>
    </div>
    <div class="card-body">
        <form method="get">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-4);">
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="nome">Nome</label>
                    <input type="text" id="nome" name="nome" class="form-input" placeholder="Buscar...">
                </div>
                <!-- Outros filtros -->
            </div>
            <div style="display: flex; gap: var(--spacing-3); justify-content: flex-end; margin-top: var(--spacing-4);">
                <a href="..." class="btn btn-secondary">Limpar</a>
                <button type="submit" class="btn btn-primary">Aplicar Filtros</button>
            </div>
        </form>
    </div>
</div>
```

**Especificações:**
- **Inputs:** Altura `40px` (menor que formulários principais, mas ainda padronizado)
- **Grid:** `minmax(200px, 1fr)` (campos menores)
- **Gap:** `var(--spacing-4)` (16px)
- **Botões:** `.btn-secondary` (Limpar) e `.btn-primary` (Aplicar)

---

## 🔷 3. BOTÕES DO MÓDULO ADMINISTRATIVO — PADRÃO SHIAI

### 3.1 Botão Primário (Ações Principais)

**HTML:**
```html
<button type="submit" class="btn btn-primary">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;">
        <!-- Ícone específico -->
    </svg>
    Texto do Botão
</button>
```

**Especificações:**
- **Background:** `var(--color-primary)` (`#3B82F6`)
- **Cor:** `var(--color-white)`
- **Altura:** `48px`
- **Padding:** `8px 16px`
- **Border-radius:** `8px`
- **Hover:** `background: var(--color-primary-hover)` | `transform: translateY(-1px)` | `box-shadow: var(--shadow-md)`

### 3.2 Botão Secundário

**HTML:**
```html
<a href="..." class="btn btn-secondary">Cancelar</a>
```

**Especificações:**
- **Background:** `var(--color-gray-100)`
- **Cor:** `var(--color-gray-700)`
- **Hover:** `background: var(--color-gray-200)`

### 3.3 Botão Outline

**HTML:**
```html
<button type="button" class="btn btn-outline">Ação</button>
```

**Especificações:**
- **Background:** `transparent`
- **Borda:** `1px solid var(--color-gray-300)`
- **Cor:** `var(--color-gray-700)`
- **Hover:** `background: var(--color-gray-50)` | `border-color: var(--color-gray-400)`

**Variante Danger:**
```html
<button type="submit" class="btn btn-outline" style="color: var(--color-danger); border-color: var(--color-danger);">Excluir</button>
```

### 3.4 Botão Ghost

**HTML:**
```html
<button type="button" class="btn btn-ghost">Ação</button>
```

**Especificações:**
- **Background:** `transparent`
- **Cor:** `var(--color-gray-700)`
- **Hover:** `background: var(--color-gray-100)`

---

## 🔷 4. ORGANIZAÇÃO DAS SEÇÕES DOS FORMULÁRIOS

### 4.1 Estrutura Hierárquica

```
page-header (título + descrição)
    ↓
card (formulário principal)
    ├── card-header (título da seção)
    └── card-body
        ├── form
        │   ├── grid (campos)
        │   └── container-buttons (botões de ação)
    ↓
card (registros/tabela - se houver)
    ├── card-header (título)
    └── card-body (lista/tabela)
```

### 4.2 Espaçamento Entre Seções

- **Entre page-header e primeiro card:** `var(--spacing-8)` (32px)
- **Entre cards:** `var(--spacing-6)` (24px)
- **Dentro do card-body:** Padding `var(--spacing-6)` (24px)

---

## 🔷 5. RESPONSIVIDADE DOS FORMULÁRIOS

### 5.1 Mobile (< 768px)

**Grid:**
```css
grid-template-columns: 1fr; /* 1 coluna */
gap: var(--spacing-4); /* Gap menor */
```

**Inputs:**
- Largura: `100%`
- Altura: `45px` (mantida)

**Cards:**
- Largura: `100%`
- Padding: `var(--spacing-4)` (16px)

**Botões:**
- Largura: `100%` (em mobile)
- Container: `flex-direction: column`

**Títulos:**
- Font-size reduzido (H1: `var(--font-size-2xl)`)

### 5.2 Tablet (768px - 1023px)

**Grid:**
```css
grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); /* 2 colunas */
gap: var(--spacing-6);
```

### 5.3 Desktop (≥ 1024px)

**Grid:**
```css
grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); /* 3+ colunas */
gap: var(--spacing-6);
```

**Botões:**
- Largura: `auto` (não 100%)
- Container: `flex-direction: row` | `justify-content: flex-end`

---

## 🔷 6. CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Base
- [ ] Verificar que todas as classes CSS estão definidas em `base.html`
- [ ] Garantir que variáveis CSS estão corretas
- [ ] Testar inputs, selects e textareas isoladamente

### Fase 2: Formulários Individuais
- [ ] Cadastros Operacionais (todos os tipos)
- [ ] Despesas
- [ ] Entradas Extras (se houver)
- [ ] Patrocínios
- [ ] Ambulância / Insumos / Estrutura
- [ ] Filtros/Busca

### Fase 3: Validação Visual
- [ ] Comparar com formulário de cadastro de atleta
- [ ] Verificar altura de inputs (45px)
- [ ] Verificar espaçamentos (gaps e margins)
- [ ] Verificar botões (altura 48px, estilo correto)
- [ ] Verificar labels (fonte, cor, espaçamento)

### Fase 4: Responsividade
- [ ] Testar mobile (< 768px)
- [ ] Testar tablet (768px - 1023px)
- [ ] Testar desktop (≥ 1024px)
- [ ] Verificar grids em cada breakpoint

### Fase 5: Interações
- [ ] Testar focus em inputs
- [ ] Testar hover em botões
- [ ] Testar validação de campos obrigatórios
- [ ] Testar máscaras (telefone, valor monetário)

---

## ✅ RESUMO FINAL

**Todos os formulários do módulo administrativo devem:**

1. ✅ Usar `.card` com `.card-header` e `.card-body`
2. ✅ Inputs com altura de `45px` (`.form-input`, `.form-select`)
3. ✅ Grid responsivo `repeat(auto-fit, minmax(300px, 1fr))` com gap `var(--spacing-6)`
4. ✅ Labels com `.form-label` e asterisco vermelho em obrigatórios
5. ✅ Botões com altura `48px` e classes `.btn-primary`, `.btn-secondary`, etc.
6. ✅ Container de botões com border-top e espaçamento correto
7. ✅ `page-header` padronizado em todas as páginas
8. ✅ Responsividade mobile-first
9. ✅ Nenhum estilo inline exceto para grid-column e margin-bottom: 0 em form-groups dentro de grids

**Nenhum formulário pode:**
- ❌ Usar estilos inline para cores, tamanhos, espaçamentos
- ❌ Ter inputs com altura diferente de 45px
- ❌ Ter grids com minmax menor que 300px (exceto filtros: 200px)
- ❌ Ter botões sem classes padronizadas
- ❌ Estar fora de um `.card`

---

**Documento criado em:** {{ data_atual }}  
**Versão:** 1.0  
**Status:** Aguardando aprovação para implementação

