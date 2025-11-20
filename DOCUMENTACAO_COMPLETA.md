# 📚 Documentação Completa do Sistema de Gestão de Competições de Judô

## 🎯 Visão Geral do Projeto

Sistema Django completo para gestão de competições de Judô do **5º Núcleo de Judô – Região Sul Fluminense**, desenvolvido para substituir planilhas Excel e automatizar todo o processo desde a inscrição de atletas até a geração de rankings e relatórios finais.

---

## 🏗️ Arquitetura e Estrutura

### Stack Tecnológico
- **Backend**: Django 5.2.8
- **API**: Django REST Framework
- **Banco de Dados**: SQLite (desenvolvimento)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Design**: Sistema de temas (Light/Dark) com CSS Variables
- **Responsividade**: Mobile-first com detecção automática

### Estrutura do Projeto
```
Shiai_sistem/
├── judocomp/              # Configurações do projeto Django
│   ├── settings.py         # Configurações principais
│   ├── urls.py            # URLs principais
│   └── wsgi.py            # WSGI config
├── atletas/               # App principal de gestão
│   ├── models.py          # Modelos de dados (8 modelos)
│   ├── views.py           # Views (40+ funções)
│   ├── urls.py            # Rotas da aplicação (78 rotas)
│   ├── utils.py           # Lógica de negócio (729 linhas)
│   ├── decorators.py      # Decoradores de permissão
│   ├── signals.py         # Sinais Django (auto-criação de UserProfile)
│   ├── middleware.py      # Detecção mobile/desktop
│   ├── admin.py           # Admin Django
│   ├── templates/         # Templates HTML (51 arquivos)
│   ├── static/            # Arquivos estáticos
│   │   ├── css/
│   │   │   ├── corporate.css  # Tema corporativo
│   │   │   └── theme.css      # Tema antigo (deprecated)
│   │   └── img/
│   │       └── logo.png
│   └── management/        # Comandos customizados (10 comandos)
└── eventos/               # App de gestão de eventos
    ├── models.py          # Modelos de eventos (3 modelos)
    ├── views.py           # Views de eventos
    ├── views_pesagem.py   # Views específicas de pesagem de eventos
    ├── urls.py            # Rotas de eventos
    └── templates/         # Templates de eventos
```

---

## 📊 Modelos de Dados

### App `atletas` (8 Modelos)

#### 1. **Academia**
```python
- nome: CharField(200)              # Nome completo da academia
- sigla: CharField(10)              # Sigla (ex: JCS, IJC)
- cidade: CharField(100)            # Cidade
- estado: CharField(2)              # Estado (UF)
- telefone: CharField(20)           # Telefone de contato
- logo: ImageField                   # Logo da academia
- senha_externa: CharField(100)     # Senha para login externo
- pontos: IntegerField(default=0)    # Pontuação total

Métodos:
- get_telefone_limpo()              # Remove caracteres não numéricos
- get_whatsapp_url(mensagem)        # Gera URL do WhatsApp
```

#### 2. **Categoria**
```python
- classe: CharField(20)             # SUB 9, SUB 11, SUB 13, SUB 15, SUB 18, SUB 21, SÊNIOR
- sexo: CharField(1)                # M (Masculino) ou F (Feminino)
- categoria_nome: CharField(100)    # Nome da categoria (ex: "Meio Leve")
- limite_min: FloatField            # Peso mínimo (kg)
- limite_max: FloatField            # Peso máximo (kg) ou 999.0 para "acima de"
- label: CharField(150)             # Rótulo completo (ex: "SUB 11 - Meio Leve")
```

#### 3. **Atleta**
```python
# Dados Pessoais
- nome: CharField(200)
- ano_nasc: IntegerField
- sexo: CharField(1)                # M ou F
- faixa: CharField(50)              # Faixa do atleta
- academia: ForeignKey(Academia)
- foto: ImageField                   # Foto do atleta

# Federação
- federado: BooleanField(default=False)
- zempo: CharField(15)            # Número ZEMPO (obrigatório se federado)

# Campos Calculados
- classe: CharField(20)            # Calculado pela idade
- categoria_nome: CharField(100)   # Categoria inicial
- categoria_limite: CharField(50)   # "x a y kg"
- peso_previsto: FloatField        # Peso informado na inscrição

# Pesagem
- peso_oficial: FloatField          # Peso registrado na pesagem
- categoria_ajustada: CharField(100) # Categoria após pesagem
- motivo_ajuste: TextField          # Motivo do ajuste
- status: CharField(30)              # OK, Eliminado Peso, Eliminado Indisciplina
- remanejado: BooleanField          # Se foi remanejado de categoria

Métodos:
- get_medalhas_count()              # Conta medalhas conquistadas
- get_participacoes_count()          # Conta participações em competições
- clean()                            # Validação: federado requer zempo
```

#### 4. **Chave**
```python
- classe: CharField(20)
- sexo: CharField(1)
- categoria: CharField(100)
- tipo_chave: CharField(20)         # olímpica, triangular, melhor_de_3
- atletas: ManyToManyField(Atleta)
- finalizada: BooleanField
```

#### 5. **Luta**
```python
- chave: ForeignKey(Chave)
- atleta1: ForeignKey(Atleta)
- atleta2: ForeignKey(Atleta)
- vencedor: ForeignKey(Atleta, null=True)
- round: IntegerField
- posicao: IntegerField
- ippon_count: IntegerField         # Contador de ippons
- pontos_perdedor: IntegerField      # Pontos do perdedor
```

#### 6. **Campeonato**
```python
- nome: CharField(200)
- data: DateField
- cidade: CharField(100)
- local: CharField(200)
- prazo_inscricao: DateField
- publicado: BooleanField           # Se está publicado no portal
- ativo: BooleanField
```

#### 7. **UserProfile**
```python
- user: OneToOneField(User)
- tipo_usuario: CharField(20)       # 'academia', 'operacional', 'admin'
- academia: ForeignKey(Academia, null=True)  # Academia vinculada (se tipo=academia)
- telefone: CharField(20)
- pode_inscricao: BooleanField
- pode_pesagem: BooleanField
- pode_chave: BooleanField
- pode_dashboard: BooleanField
```

#### 8. **AdminLog**
```python
- data_hora: DateTimeField
- tipo: CharField(20)               # REMANEJAMENTO, DESCLASSIFICACAO, PESAGEM, OUTRO
- acao: CharField(200)
- atleta: ForeignKey(Atleta, null=True)
- academia: ForeignKey(Academia, null=True)
- detalhes: TextField                # Informações adicionais
- usuario_ip: GenericIPAddressField
```

### App `eventos` (3 Modelos)

#### 1. **Evento**
```python
- nome: CharField(200)
- descricao: TextField
- local: CharField(200)
- data_evento: DateField
- data_limite_inscricao: DateField
- regulamento: FileField             # PDF do regulamento
- parametros_baseado_em: ForeignKey('self')  # Clonar parâmetros de outro evento
- valor_federado: DecimalField       # Valor para atletas federados
- valor_nao_federado: DecimalField  # Valor para não federados
- pesagem_encerrada: BooleanField   # Se a pesagem foi encerrada
- ativo: BooleanField
- created_at: DateTimeField
- updated_at: DateTimeField

Propriedades:
- is_inscricao_aberta                # Verifica se ainda aceita inscrições
```

#### 2. **EventoParametro**
```python
- evento: OneToOneField(Evento)
- idade_min: IntegerField(default=3)
- idade_max: IntegerField(default=99)
- usar_pesagem: BooleanField
- usar_chaves_automaticas: BooleanField
- permitir_festival: BooleanField
- pontuacao_primeiro: IntegerField(default=10)
- pontuacao_segundo: IntegerField(default=7)
- pontuacao_terceiro: IntegerField(default=5)
- penalidade_remanejamento: IntegerField(default=1)
```

#### 3. **Inscricao**
```python
- evento: ForeignKey(Evento)
- atleta: ForeignKey(Atleta)
- academia: ForeignKey(Academia)
- inscrito_por: ForeignKey(User)
- data_inscricao: DateTimeField
- observacao: TextField
- status_pesagem: CharField(20)     # PENDENTE, OK, REMANEJADO, DESC
- status: CharField(30)              # Inscrito, Pesado, Desclassificado, Remanejado
- peso_oficial: FloatField           # Peso registrado na pesagem
- categoria_ajustada: CharField(100) # Categoria após pesagem
- valor_inscricao: DecimalField      # Valor pago na inscrição

Unique Together: (evento, atleta)   # Um atleta só pode se inscrever uma vez por evento
```

---

## 🎨 Sistema de Design e Interface

### Tema Corporativo (corporate.css)

#### Cores Principais (Light Theme)
```css
--bg: #F5F5F5                    # Fundo principal
--card-bg: #FFFFFF               # Fundo de cards
--text: #1A1A1A                  # Texto principal
--text-sec: #555                  # Texto secundário
--border: #D9D9D9                # Bordas
--primary: #1976D2               # Azul primário
--corporate-blue: #0A2342        # Azul institucional CBJ/FJERJ
--success: #46C97A               # Verde (OK)
--danger: #D9534F                 # Vermelho (erro/desclassificação)
--warning: #E4B000               # Amarelo (remanejamento)
--shadow: rgba(0,0,0,0.1)        # Sombra
```

#### Cores Principais (Dark Theme)
```css
--bg: #1A1A1A                    # Fundo principal
--card-bg: #2A2A2A               # Fundo de cards
--text: #EEE                     # Texto principal
--text-sec: #BBB                  # Texto secundário
--border: #444                    # Bordas
--primary: #64B5F6               # Azul primário
--corporate-blue: #1E3A60        # Azul institucional
--success: #66BB6A               # Verde
--danger: #EF5350                 # Vermelho
--warning: #FFA726               # Amarelo
```

### Componentes Visuais

#### Sidebar
- **Largura**: 250px (desktop)
- **Background**: Branco (light) / #1F1F1F (dark)
- **Menu agrupado**:
  - **INSTITUCIONAL**: Home, Academias, Atletas, Cadastrar Atleta
  - **COMPETIÇÃO**: Pesagem, Chaves, Ranking, Relatórios
  - **EVENTOS**: Gerenciar Eventos (operacional) / Eventos Disponíveis (academia)
  - **SISTEMA**: Dashboard, Resetar Campeonato, Configurações
- **Ícones**: Emojis grandes e alinhados
- **Hover**: Efeito suave com background colorido
- **Divisores**: Entre grupos de menu

#### Page Header
- **Background**: Azul institucional (#0A2342)
- **Estrutura**:
  - Logo + Título institucional
  - Botões de ação (direita)
- **Título**: Branco com text-shadow
- **Responsivo**: Stack vertical no mobile

#### Cards
- **Background**: Branco (light) / #2A2A2A (dark)
- **Border-radius**: 8px
- **Sombra**: Suave (0 1px 3px)
- **Padding**: 24px
- **Hover**: Elevação sutil

#### Tabelas
- **Header**: Azul institucional com texto branco
- **Linhas**: Alternância de cor (zebra)
- **Hover**: Background suave
- **Bordas**: Discretas
- **Responsivo**: Scroll horizontal no mobile

#### Botões
- **Primário**: Azul institucional, texto branco
- **Secundário**: Branco, borda azul
- **Sucesso**: Verde (#46C97A)
- **Perigo**: Vermelho (#D9534F)
- **Aviso**: Amarelo (#E4B000)
- **WhatsApp**: Verde (#25D366)

---

## 🔐 Sistema de Autenticação e Permissões

### Tipos de Usuário

#### 1. **Academia** (Professor)
- Acesso ao painel da academia (`/academia/painel/`)
- Vê apenas atletas da sua academia
- Pode cadastrar novos atletas (vinculados automaticamente)
- Pode inscrever atletas em eventos
- **Menu específico**:
  - Painel
  - Cadastrar Atleta
  - Meus Atletas
  - Eventos Disponíveis

#### 2. **Operacional** (Organizador)
- Acesso ao sistema completo (`/`)
- Vê todos os atletas e academias
- Pode criar/editar eventos
- Pode realizar pesagem
- Pode gerar chaves
- **Menu completo** do sistema

#### 3. **Admin** (Superusuário)
- Mesmas permissões do operacional
- Acesso ao Django Admin (`/admin/`)
- Pode resetar campeonato

### Fluxo de Login

1. **Tela de Escolha** (`/login/tipo/`):
   - Botão "Login da Academia"
   - Botão "Login Operacional"

2. **Login Academia** (`/login/academia/`):
   - Username e senha
   - Valida `tipo_usuario == 'academia'`
   - Redireciona para `/academia/painel/`

3. **Login Operacional** (`/login/operacional/`):
   - Username e senha
   - Valida `tipo_usuario == 'operacional'` ou `is_superuser`
   - Redireciona para `/` (index)

### Decoradores de Permissão

```python
@academia_required      # Apenas usuários tipo 'academia'
@operacional_required   # Apenas usuários tipo 'operacional' ou admin
@admin_required         # Apenas superusuários
```

---

## 🌐 Portal Público

### Rota: `/portal/`

#### Funcionalidades
- **Navbar**: Logo, menu (Home, Notícias, Eventos, Calendário, Shiken, Contato), botão Login, toggle de tema
- **Hero Section**: 
  - Título: "Judô na Costa Verde – Sistema Oficial de Inscrições"
  - Botões: "Ver Eventos" e "Área da Academia"
- **Eventos Públicos**: Lista eventos com `publicado=True`
  - Nome, data, local, prazo de inscrição
  - Botões: "Ver Regulamento" e "Inscrever Atletas"
- **Notícias**: 3 colunas (CBJ, FJERJ, 5º Núcleo)
- **Calendário**: Eventos unificados
- **Marketing**: Seções para SHIKEN, Sistema de Eventos, Judô Kids

### Design
- Tema corporativo (light/dark)
- Layout limpo e profissional
- Sem sidebar (template `public_base.html`)

---

## 📋 Funcionalidades Principais

### 1. Gestão de Academias

#### Listagem (`/academias/`)
- **Visual**: Cards (ou tabela, conforme implementação)
- **Informações**: Logo, nome, sigla, cidade, estado, telefone
- **Ações**:
  - ✏️ Editar
  - 👥 Ver Atletas
  - 📲 WhatsApp (link automático)
  - 🗑️ Excluir

#### Cadastro/Edição
- Campos: Nome, Sigla, Cidade, Estado, Telefone, Logo
- Upload de logo (ImageField)
- Validação de campos obrigatórios

### 2. Gestão de Atletas

#### Listagem (`/atletas/`)
- **Visual**: Cards em grid responsivo
- **Informações por card**:
  - Foto (128x128) ou placeholder
  - Nome, Classe, Sexo, Faixa
  - Academia (com sigla)
  - Categoria atual
  - Peso oficial (se existir)
  - Status federado (✔/✘) e ZEMPO
  - Medalhas e participações
- **Ações**:
  - ✏️ Editar (cadastro básico)
  - 👁️ Ver Detalhes
- **Filtros**: Nome, classe, sexo, categoria, academia

#### Cadastro (`/atletas/cadastrar/`)
- **Campos obrigatórios**:
  - Nome completo
  - Ano de nascimento
  - Sexo
  - Faixa
  - Academia (auto-preenchido se academia logada)
- **Campos opcionais**:
  - Telefone
  - Foto
- **Federação**:
  - Checkbox "É Federado?"
  - Campo ZEMPO (obrigatório se federado)
- **Tipo de Atleta**:
  - Competidor (normal)
  - Festival (3-6 anos)
- **Cálculo automático**:
  - Classe (baseada na idade)
  - Categorias disponíveis (filtradas por classe e sexo)

#### Edição (`/atletas/<id>/editar/`)
- **Campos editáveis**:
  - Nome
  - Ano de nascimento
  - Sexo
  - Faixa
  - Academia (apenas operacional)
  - Federado/ZEMPO
  - Foto
- **Não editável**: Categoria, peso oficial (editar via pesagem)

#### Detalhes (`/atletas/<id>/`)
- **Header**: Foto grande, nome, informações básicas
- **Seções**:
  - Informações Gerais (idade, classe, categoria, peso, status)
  - Estatísticas (medalhas, participações)
  - Histórico de Competições
- **Ações**: Editar, WhatsApp Academia, Voltar

#### Importação CSV (`/atletas/importar/`)
- Upload de arquivo CSV
- Validação de colunas obrigatórias
- Feedback detalhado (sucessos e erros)
- Suporte a múltiplos formatos

### 3. Sistema de Pesagem

#### Tela Principal (`/pesagem/`)
- **Filtros** (uma linha):
  - Classe (dropdown)
  - Sexo (dropdown)
  - Categoria (dropdown)
  - Botões: Filtrar, Limpar
- **Tabela**:
  - Colunas: Nome, Classe, Sexo, Categoria, Limite, Peso Oficial, Status, Ações
  - Formulário inline por linha: Input peso + Botão Registrar
- **Status Badges**:
  - OK (verde)
  - REMANEJADO (amarelo)
  - DESCLASSIFICADO (vermelho)
  - PENDENTE (cinza)

#### Lógica de Pesagem

##### Cenário A: Peso dentro da categoria
1. Operador registra peso
2. Sistema verifica limites da categoria atual
3. Se dentro → **Salva automaticamente**, status = OK
4. **Sem modal**, atualização via AJAX

##### Cenário B: Peso fora da categoria (com categoria sugerida)
1. Operador registra peso
2. Sistema verifica limites → **Fora**
3. Sistema busca categoria sugerida (baseada no peso)
4. **Exibe modal obrigatório** com:
   - Nome do atleta
   - Peso registrado
   - Categoria atual + limites
   - Categoria sugerida + limites
   - Texto explicativo
5. **3 botões**:
   - 🔄 **Remanejar**: Move para nova categoria, academia perde 1 ponto
   - ❌ **Desclassificar**: Marca como eliminado
   - 🔙 **Cancelar**: Não salva nada, fecha modal

##### Cenário C: Peso fora de todas as categorias
1. Operador registra peso
2. Sistema verifica → **Fora de todas**
3. **Exibe modal** apenas com:
   - Botão Desclassificar
   - Botão Cancelar
   - (Sem opção de remanejar)

#### Endpoints de Pesagem
- `POST /pesagem/<atleta_id>/registrar/` - Valida peso, retorna JSON
- `POST /pesagem/<atleta_id>/remanejar/` - Processa remanejamento
- `POST /pesagem/<atleta_id>/desclassificar/` - Processa desclassificação

### 4. Sistema de Eventos

#### Módulo Completo (`eventos/`)

##### Para Operacional

**Listar Eventos** (`/operacional/eventos/`)
- Tabela com todos os eventos
- Ações: Criar, Editar, Configurar, Ver Inscritos, **Pesagem**

**Criar Evento** (`/operacional/eventos/criar/`)
- Campos:
  - Nome, Descrição, Local
  - Data do evento
  - Data limite de inscrição
  - Regulamento (PDF)
  - Valores: Federado e Não Federado
- Opção: Clonar parâmetros de evento anterior

**Configurar Evento** (`/operacional/eventos/<id>/configurar/`)
- Parâmetros:
  - Idade mínima/máxima
  - Usar pesagem
  - Usar chaves automáticas
  - Permitir festival
  - Pontuações (1º, 2º, 3º lugar)
  - Penalidade de remanejamento

**Ver Inscritos** (`/operacional/eventos/<id>/inscritos/`)
- Tabela com todos os inscritos
- Colunas: Nome, Academia, Classe, Sexo, Faixa, Federado, Status, Valor, Data

**Pesagem do Evento** (`/operacional/eventos/<id>/pesagem/`)
- Similar à pesagem geral, mas filtrada por evento
- Usa modelo `Inscricao` ao invés de `Atleta`
- Mesma lógica de modal e confirmação

##### Para Academia

**Eventos Disponíveis** (`/academia/eventos/`)
- Cards com eventos abertos para inscrição
- Informações: Nome, data, local, prazo
- Botão: "Inscrever Atletas"

**Inscrever Atletas** (`/academia/eventos/<id>/inscrever/`)
- Lista de atletas da academia em cards
- Checkboxes para seleção múltipla
- Filtros: Nome, classe
- Validação: Federado sem ZEMPO → bloqueia inscrição
- Cálculo automático do valor (federado vs não federado)
- Botão: "Cadastrar Novo Atleta" (abre modal rápido)

**Cadastrar Atleta Rápido** (`/academia/eventos/<id>/novo-atleta/`)
- Formulário simplificado:
  - Nome, Ano nascimento, Sexo, Faixa
  - Federado/ZEMPO
  - Academia (auto-preenchido)
- Após salvar: Retorna à lista e marca atleta automaticamente

**Meus Inscritos** (`/academia/eventos/<id>/meus-inscritos/`)
- Tabela com atletas inscritos no evento
- Status de pesagem
- Peso oficial (se pesado)

### 5. Geração de Chaves

#### Tipos de Chave
- **Olímpica**: Eliminação simples
- **Triangular**: 3 atletas, todos lutam contra todos
- **Melhor de 3**: Série de 3 lutas

#### Geração Automática
- Seleciona atletas por classe, sexo e categoria
- Cria estrutura de lutas automaticamente
- Distribui atletas nas posições

#### Geração Manual
- Seleção livre de atletas
- Criação de lutas casadas (não conta para ranking)

### 6. Registro de Lutas

#### Interface Desktop
- Visualização completa da chave
- Botões para registrar vencedor
- Atualização automática da próxima luta

#### Interface Mobile (`/chave/mobile/<id>/`)
- Layout otimizado para tela pequena
- Botões grandes e fáceis de tocar
- Navegação simplificada

### 7. Ranking e Pontuação

#### Cálculo de Pontos
- **1º lugar**: 10 pontos (configurável)
- **2º lugar**: 7 pontos (configurável)
- **3º lugar**: 5 pontos (configurável)
- **Festival**: 1 ponto automático
- **Remanejamento**: -1 ponto (penalidade)

#### Ranking de Academias (`/ranking/`)
- Tabela ordenada por pontos
- Colunas: Posição, Academia, Pontos
- Atualização em tempo real

### 8. Relatórios

#### Dashboard (`/relatorios/dashboard/`)
- Estatísticas gerais:
  - Total de atletas
  - Atletas OK
  - Total de academias
  - Total de categorias
  - Pesagens realizadas
  - Top 5 academias

#### Relatório de Atletas Inscritos
- Lista completa de atletas
- Filtros aplicáveis
- Exportável

#### Relatório de Pesagem Final
- Todos os atletas pesados
- Status de cada um
- Categorias ajustadas

#### Relatório de Chaves
- Todas as chaves geradas
- Resultados finais
- Pódios

#### Relatório de Resultados por Categoria
- Detalhamento por categoria
- Colocações
- Pontuações

---

## 🎨 Design System e Responsividade

### Breakpoints
- **Desktop**: > 768px (sidebar fixa, layout completo)
- **Mobile**: ≤ 768px (menu hambúrguer, layout empilhado)

### Componentes Reutilizáveis

#### Cards
- `.atleta-card`: Card de atleta
- `.academia-card`: Card de academia
- `.evento-card`: Card de evento

#### Badges
- `.status-badge`: Badge de status
- `.status-ok`: Verde
- `.status-remanejado`: Amarelo
- `.status-desclassificado`: Vermelho
- `.status-pendente`: Cinza

#### Botões
- `.btn`: Botão padrão
- `.btn-primary`: Azul institucional
- `.btn-secondary`: Branco com borda
- `.btn-success`: Verde
- `.btn-danger`: Vermelho
- `.btn-warning`: Amarelo

#### Modais
- `.modal-overlay`: Overlay escuro
- `.modal-content`: Conteúdo do modal
- `.modal-title`: Título do modal
- `.modal-body`: Corpo do modal
- `.modal-actions`: Área de botões

---

## 🔧 Utilitários e Funções Auxiliares

### `utils.py` (729 linhas)

#### Cálculo de Classe
```python
calcular_classe(ano_nasc) → 'SUB 9', 'SUB 11', etc.
```

#### Ajuste de Categoria por Peso
```python
ajustar_categoria_por_peso(atleta, peso) → (categoria, motivo)
```

#### Geração de Chaves
```python
gerar_chave(categoria, classe, sexo) → Chave object
```

#### Cálculo de Pontuação
```python
calcular_pontuacao_academias() → dict
```

#### Determinação de Categoria por Peso
```python
categoria_por_peso(classe, sexo, peso) → Categoria object ou None
```

---

## 📱 Comandos de Gerenciamento

### 10 Comandos Customizados

1. **`popular_categorias`**: Popula categorias oficiais do JSON
2. **`recalcular_classes_atletas`**: Recalcula classes de todos os atletas
3. **`gerar_todas_chaves`**: Gera chaves para todas as categorias
4. **`aprovar_todos_pesagem`**: Aprova todos os atletas na pesagem
5. **`corrigir_categorias_extra_ligeiro`**: Corrige categorias específicas
6. **`corrigir_classes_verbo_divino`**: Corrige classes específicas
7. **`corrigir_limites_categorias`**: Corrige limites de categorias
8. **`importar_festival_verbo_divino`**: Importa dados específicos
9. **`importar_verbo_divino_inclusao`**: Importa inclusões específicas
10. **Outros comandos de manutenção**

---

## 🔄 Fluxos de Trabalho

### Fluxo Completo de uma Competição

1. **Configuração Inicial**
   - Cadastrar academias
   - Popular categorias oficiais
   - Criar evento (operacional)

2. **Inscrições**
   - Academias inscrevem atletas via portal
   - Ou operacional cadastra diretamente
   - Sistema valida dados (federado requer ZEMPO)
   - Calcula valor da inscrição

3. **Pesagem**
   - Operacional acessa pesagem do evento
   - Registra peso de cada atleta
   - Sistema valida categoria
   - Modal de confirmação (se necessário)
   - Aplica remanejamento ou desclassificação

4. **Geração de Chaves**
   - Operacional gera chaves por categoria
   - Sistema distribui atletas automaticamente

5. **Registro de Lutas**
   - Operacional registra vencedores
   - Sistema atualiza chave automaticamente
   - Define pódio final

6. **Cálculo de Pontuação**
   - Sistema calcula pontos de todas as academias
   - Atualiza ranking

7. **Relatórios**
   - Geração de relatórios finais
   - Dashboard com estatísticas

---

## 📊 Estatísticas do Projeto

### Código
- **Models**: 11 modelos (8 em `atletas`, 3 em `eventos`)
- **Views**: 40+ funções
- **Templates**: 51 arquivos HTML
- **URLs**: 78 rotas
- **Utils**: 729 linhas de lógica de negócio
- **Comandos**: 10 comandos customizados
- **CSS**: 2 arquivos (corporate.css principal)

### Funcionalidades
- ✅ 100% das funcionalidades básicas implementadas
- ✅ Sistema de autenticação dual (academia/operacional)
- ✅ Portal público
- ✅ Sistema de eventos completo
- ✅ Pesagem com modal de confirmação
- ✅ Interface responsiva (mobile + desktop)
- ✅ Sistema de relatórios completo
- ✅ API REST para ranking
- ✅ Importação de dados via CSV
- ✅ Sistema de logs administrativos
- ✅ Tema claro/escuro
- ✅ Design corporativo institucional

---

## 🔐 Segurança

### Implementado
- ✅ CSRF Protection
- ✅ Decoradores de permissão
- ✅ Validação de dados (models.clean())
- ✅ Sanitização de uploads
- ✅ Proteção contra SQL Injection (ORM Django)
- ✅ Validação de tipos de usuário

### Recomendações para Produção
- ⚠️ Mover SECRET_KEY para variável de ambiente
- ⚠️ Definir ALLOWED_HOSTS específicos
- ⚠️ DEBUG = False
- ⚠️ Configurar banco PostgreSQL/MySQL
- ⚠️ Configurar HTTPS
- ⚠️ Implementar rate limiting
- ⚠️ Backup automático do banco

---

## 🚀 Melhorias Recentes Implementadas

### 1. Reformulação Visual Corporativa
- ✅ Tema corporativo CBJ/FJERJ
- ✅ Cores institucionais (#0A2342)
- ✅ Sidebar redesenhada
- ✅ Cards modernos
- ✅ Tabelas profissionais

### 2. Sistema de Eventos
- ✅ Módulo completo de eventos
- ✅ Inscrições por evento
- ✅ Pesagem por evento
- ✅ Valores diferenciados (federado/não federado)

### 3. Sistema de Federação
- ✅ Campo "Federado" em atletas
- ✅ Campo ZEMPO (obrigatório se federado)
- ✅ Validação automática
- ✅ Exibição em cards e listas

### 4. Pesagem Robusta
- ✅ Modal obrigatório para confirmação
- ✅ Endpoints separados (remanejar/desclassificar)
- ✅ Nenhuma ação automática sem confirmação
- ✅ Logs de todas as ações

### 5. Portal Público
- ✅ Landing page institucional
- ✅ Listagem de eventos públicos
- ✅ Login diferenciado (academia/operacional)

### 6. Edição de Atletas
- ✅ View e template de edição
- ✅ Separação clara: edição vs pesagem
- ✅ Validação de permissões

---

## 📝 Observações Importantes

- Sistema usa SQLite em desenvolvimento (migrar para PostgreSQL em produção)
- Middleware mobile funciona automaticamente
- Reset de campeonato requer senha de administrador
- Todos os títulos sobre fundo azul usam texto branco
- Sistema de temas (light/dark) aplicado globalmente
- Sidebar só aparece para usuários autenticados
- Portal público usa template separado (sem sidebar)

---

## 🎯 Próximos Passos Sugeridos

1. **Exportação PDF**: Gerar relatórios em PDF
2. **Notificações**: Email/SMS para academias
3. **Dashboard Avançado**: Gráficos e estatísticas visuais
4. **API Completa**: REST API para integrações
5. **App Mobile**: Aplicativo nativo
6. **Pagamento Online**: Integração com gateway de pagamento
7. **Certificados**: Geração automática de certificados

---

**Documentação gerada em**: 2025
**Versão do Sistema**: 2.0
**Última atualização**: Implementação completa de eventos e pesagem robusta

