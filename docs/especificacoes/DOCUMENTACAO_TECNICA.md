'# 📚 Documentação Técnica - SHIAI SISTEM

**Versão:** 1.0  
**Data:** 2024  
**Para:** Desenvolvedores

---

## 📋 Índice

1. [Models](#1-models)
2. [Views](#2-views)
3. [URLs](#3-urls)
4. [Templates](#4-templates)
5. [Lógica de Negócio](#5-lógica-de-negócio)
6. [Segurança](#6-segurança)

---

## 1. Models

### 1.1 Academia

**Descrição:** Representa uma academia de Judô participante do sistema.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `nome` | CharField(200) | Nome da academia | Sim |
| `cidade` | CharField(100) | Cidade da academia | Sim |
| `estado` | CharField(2) | Estado (UF) | Sim |
| `telefone` | CharField(20) | Telefone de contato | Não |
| `responsavel` | CharField(200) | Nome do responsável | Não |
| `pontos` | IntegerField | Pontos acumulados (global) | Não (default: 0) |
| `foto_perfil` | ImageField | Foto de perfil da academia | Não |
| `login` | CharField(100) | Login único da academia | Não (unique) |
| `senha_login` | CharField(128) | Senha criptografada (SHA256) | Não |
| `ativo_login` | BooleanField | Permite login da academia | Não (default: True) |
| `bonus_percentual` | DecimalField(5,2) | Bônus % sobre inscrições | Não |
| `bonus_fixo` | DecimalField(10,2) | Bônus fixo por atleta | Não |

**Relações:**
- `OneToMany` → `Atleta` (via `atleta.academia`)
- `OneToMany` → `AcademiaPontuacao` (via `pontuacoes`)
- `OneToMany` → `AcademiaCampeonatoSenha` (via `senhas_campeonatos`)

**Métodos:**
- `verificar_senha(senha: str) -> bool`: Verifica senha usando SHA256
- `definir_senha(senha: str)`: Define senha com hash SHA256

**Lógica:**
- Login único por academia
- Senha armazenada como hash SHA256
- Bônus pode ser percentual ou fixo (não ambos simultaneamente)

---

### 1.2 Atleta

**Descrição:** Cadastro global permanente do atleta (não vinculado a evento específico).

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `nome` | CharField(200) | Nome completo | Sim |
| `data_nascimento` | DateField | Data de nascimento | Sim |
| `ano_nasc` | IntegerField | Ano de nascimento (legado) | Não |
| `sexo` | CharField(1) | M ou F | Sim |
| `academia` | ForeignKey(Academia) | Academia do atleta | Sim |
| `classe_inicial` | CharField(20) | Classe calculada | Não |
| `documento_oficial` | FileField | Documento de identidade | Não |
| `foto_perfil` | ImageField | Foto de perfil | Não |
| `status_ativo` | BooleanField | Atleta ativo | Não (default: True) |
| `faixa` | CharField(20) | Faixa do atleta | Não |
| `federado` | BooleanField | É federado | Não (default: False) |
| `numero_zempo` | CharField(50) | Número Zempo | Não (obrigatório se federado) |
| `data_cadastro` | DateTimeField | Data de cadastro | Auto |
| `data_atualizacao` | DateTimeField | Última atualização | Auto |

**Relações:**
- `ManyToOne` → `Academia` (via `academia`)
- `ManyToMany` → `Chave` (via `chaves`)
- `OneToMany` → `Inscricao` (via `inscricoes`)
- `OneToMany` → `Luta` (como `atleta_a`, `atleta_b`, `vencedor`)

**Properties:**
- `idade`: Calcula idade baseada em `data_nascimento`
- `get_ano_nasc()`: Retorna ano de nascimento (compatibilidade)
- `tem_documento()`: Verifica se tem documento oficial
- `get_classe_atual()`: Calcula classe atual baseada na idade

**Lógica:**
- Classe inicial calculada automaticamente na criação
- Atleta pode ter múltiplas inscrições em diferentes campeonatos
- Documento obrigatório apenas para inscrição (não para cadastro)

---

### 1.3 Categoria

**Descrição:** Categoria oficial de competição (classe, sexo, peso).

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `classe` | CharField(20) | Classe (SUB 9, SUB 11, etc.) | Sim |
| `sexo` | CharField(1) | M ou F | Sim |
| `categoria_nome` | CharField(100) | Nome da categoria | Sim |
| `limite_min` | FloatField | Peso mínimo (kg) | Sim |
| `limite_max` | FloatField | Peso máximo (kg) | Sim |
| `label` | CharField(150) | Label completo | Sim |

**Relações:**
- Nenhuma (modelo independente)

**Lógica:**
- Ordenação: classe → sexo → limite_min
- Label formatado: "SUB 11 - Meio Leve"

---

### 1.4 Campeonato

**Descrição:** Representa um evento/campeonato específico.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `nome` | CharField(200) | Nome do campeonato | Sim |
| `data_inicio` | DateField | Data início inscrições | Não |
| `data_competicao` | DateField | Data da competição | Não |
| `data_limite_inscricao` | DateField | Data limite inscrições | Não |
| `ativo` | BooleanField | Campeonato ativo | Não (default: True) |
| `regulamento` | TextField | Regulamento do evento | Não |
| `valor_inscricao_federado` | DecimalField(10,2) | Valor para federados | Não |
| `valor_inscricao_nao_federado` | DecimalField(10,2) | Valor para não federados | Não |

**Relações:**
- `OneToMany` → `Inscricao` (via `inscricoes`)
- `OneToMany` → `Chave` (via `chaves`)
- `OneToMany` → `AcademiaPontuacao` (via `pontuacoes`)
- `OneToMany` → `Despesa` (via `despesas`)
- `OneToMany` → `AcademiaCampeonatoSenha` (via `senhas_academias`)

**Lógica:**
- Apenas um campeonato pode estar ativo por vez
- Valores de inscrição diferenciados por status federado

---

### 1.5 Inscricao

**Descrição:** Inscrição de um atleta em um campeonato específico.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `atleta` | ForeignKey(Atleta) | Atleta inscrito | Sim |
| `campeonato` | ForeignKey(Campeonato) | Campeonato | Sim |
| `classe_escolhida` | CharField(20) | Classe escolhida | Sim |
| `categoria_escolhida` | CharField(100) | Categoria escolhida | Sim |
| `peso` | FloatField | Peso oficial (kg) | Não |
| `categoria_ajustada` | CharField(100) | Categoria após pesagem | Não |
| `motivo_ajuste` | TextField | Motivo do ajuste | Não |
| `remanejado` | BooleanField | Foi remanejado | Não (default: False) |
| `status_inscricao` | CharField(20) | Status da inscrição | Não (default: 'pendente') |
| `data_inscricao` | DateTimeField | Data da inscrição | Auto |
| `data_pesagem` | DateTimeField | Data da pesagem | Não |

**Relações:**
- `ManyToOne` → `Atleta` (via `atleta`)
- `ManyToOne` → `Campeonato` (via `campeonato`)

**Constraints:**
- `unique_together`: (`atleta`, `campeonato`, `classe_escolhida`, `categoria_escolhida`)

**Status:**
- `pendente`: Aguardando confirmação
- `confirmado`: Confirmado pelo organizador (conta para caixa)
- `aprovado`: Aprovado para gerar chave (após pesagem)
- `reprovado`: Reprovado na pesagem

**Métodos:**
- `pode_gerar_chave() -> bool`: Verifica se está apta para gerar chave

**Lógica:**
- Atleta pode ter múltiplas inscrições no mesmo campeonato (diferentes classes/categorias)
- Categoria pode ser ajustada após pesagem
- Status determina se pode gerar chave

---

### 1.6 Chave

**Descrição:** Chave de competição para uma categoria específica.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `campeonato` | ForeignKey(Campeonato) | Campeonato | Não |
| `classe` | CharField(20) | Classe da chave | Sim |
| `sexo` | CharField(1) | M ou F | Sim |
| `categoria` | CharField(100) | Nome da categoria | Sim |
| `estrutura` | JSONField | Estrutura da chave | Não (default: {}) |

**Relações:**
- `ManyToOne` → `Campeonato` (via `campeonato`)
- `ManyToMany` → `Atleta` (via `atletas`)
- `OneToMany` → `Luta` (via `lutas`)

**Lógica:**
- Estrutura JSON armazena tipo de chave e IDs das lutas
- Ordenação: campeonato → classe → sexo → categoria

---

### 1.7 Luta

**Descrição:** Representa uma luta individual dentro de uma chave.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `chave` | ForeignKey(Chave) | Chave da luta | Sim |
| `atleta_a` | ForeignKey(Atleta) | Atleta lado A (azul) | Não |
| `atleta_b` | ForeignKey(Atleta) | Atleta lado B (branco) | Não |
| `vencedor` | ForeignKey(Atleta) | Atleta vencedor | Não |
| `round` | IntegerField | Round da chave | Sim |
| `proxima_luta` | IntegerField | ID da próxima luta | Não |
| `concluida` | BooleanField | Luta concluída | Não (default: False) |
| `tipo_vitoria` | CharField(20) | Tipo de vitória | Não |
| `pontos_vencedor` | IntegerField | Pontos do vencedor | Não (default: 0) |
| `pontos_perdedor` | IntegerField | Pontos do perdedor | Não (default: 0) |
| `ippon_count` | IntegerField | Contador de Ippons | Não (default: 0) |
| `wazari_count` | IntegerField | Contador de Wazaris | Não (default: 0) |
| `yuko_count` | IntegerField | Contador de Yukos | Não (default: 0) |

**Relações:**
- `ManyToOne` → `Chave` (via `chave`)
- `ManyToOne` → `Atleta` (como `atleta_a`, `atleta_b`, `vencedor`)

**Tipos de Vitória:**
- `IPPON`: Vitória por Ippon
- `WAZARI`: Vitória por Wazari
- `YUKO`: Vitória por Yuko

**Lógica:**
- `proxima_luta` define estrutura de avanço na chave
- Round 1 = primeira fase, Round 2 = semifinal, etc.

---

### 1.8 AcademiaPontuacao

**Descrição:** Pontuação de uma academia em um campeonato específico.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `campeonato` | ForeignKey(Campeonato) | Campeonato | Sim |
| `academia` | ForeignKey(Academia) | Academia | Sim |
| `ouro` | IntegerField | Medalhas de ouro | Não (default: 0) |
| `prata` | IntegerField | Medalhas de prata | Não (default: 0) |
| `bronze` | IntegerField | Medalhas de bronze | Não (default: 0) |
| `quarto` | IntegerField | 4º lugares | Não (default: 0) |
| `quinto` | IntegerField | 5º lugares | Não (default: 0) |
| `festival` | IntegerField | Participações em festival | Não (default: 0) |
| `remanejamento` | IntegerField | Remanejamentos | Não (default: 0) |
| `pontos_totais` | IntegerField | Pontos totais | Não (default: 0) |

**Relações:**
- `ManyToOne` → `Campeonato` (via `campeonato`)
- `ManyToOne` → `Academia` (via `academia`)

**Constraints:**
- `unique_together`: (`campeonato`, `academia`)

**Lógica:**
- Pontos totais calculados: Ouro(10) + Prata(7) + Bronze(5) + Quarto(3) + Quinto(1)

---

### 1.9 Despesa

**Descrição:** Despesa do campeonato.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `campeonato` | ForeignKey(Campeonato) | Campeonato | Sim |
| `categoria` | CharField(50) | Categoria da despesa | Sim |
| `nome` | CharField(200) | Nome da despesa | Sim |
| `valor` | DecimalField(10,2) | Valor | Sim |
| `status` | CharField(20) | Status (pago/pendente) | Não (default: 'pendente') |
| `observacao` | TextField | Observação | Não |
| `contato_nome` | CharField(200) | Nome do contato | Não |
| `contato_whatsapp` | CharField(20) | WhatsApp do contato | Não |
| `data_cadastro` | DateTimeField | Data de cadastro | Auto |
| `data_pagamento` | DateField | Data de pagamento | Não |

**Categorias:**
- `arbitros`, `mesarios`, `coordenadores`, `oficiais_pesagem`, `oficiais_mesa`
- `insumos`, `ambulancia`, `patrocinios`, `estrutura`, `limpeza`, `outras`

---

### 1.10 CadastroOperacional

**Descrição:** Cadastros operacionais (árbitros, mesários, etc.).

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `tipo` | CharField(50) | Tipo de cadastro | Sim |
| `nome` | CharField(200) | Nome | Sim |
| `telefone` | CharField(20) | Telefone | Não |
| `observacao` | TextField | Observação | Não |
| `data_cadastro` | DateTimeField | Data de cadastro | Auto |
| `ativo` | BooleanField | Ativo | Não (default: True) |

**Tipos:**
- `arbitro`, `mesario`, `coordenador`, `oficial_pesagem`, `oficial_mesa`
- `ambulancia`, `patrocinador`, `insumo`

---

### 1.11 UsuarioOperacional

**Descrição:** Perfil de usuário operacional com permissões e expiração.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `user` | OneToOneField(User) | Usuário Django | Sim |
| `pode_resetar_campeonato` | BooleanField | Pode resetar campeonato | Não (default: False) |
| `pode_criar_usuarios` | BooleanField | Pode criar usuários | Não (default: False) |
| `data_expiracao` | DateTimeField | Data de expiração | Não (null = vitalício) |
| `criado_por` | ForeignKey(User) | Usuário criador | Não |
| `data_criacao` | DateTimeField | Data de criação | Auto |
| `ativo` | BooleanField | Perfil ativo | Não (default: True) |

**Relações:**
- `OneToOne` → `User` (via `user`)
- `ManyToOne` → `User` (via `criado_por`)

**Properties:**
- `esta_expirado`: Verifica se acesso expirou
- `dias_restantes`: Retorna dias até expiração

**Lógica:**
- Apenas usuário principal tem `pode_resetar_campeonato = True`
- Apenas usuário principal tem `pode_criar_usuarios = True`
- Usuários criados têm validade de 30 dias (padrão)

---

### 1.12 AcademiaCampeonatoSenha

**Descrição:** Senha única por campeonato para cada academia.

**Campos:**

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `id` | AutoField | Chave primária | Auto |
| `academia` | ForeignKey(Academia) | Academia | Sim |
| `campeonato` | ForeignKey(Campeonato) | Campeonato | Sim |
| `senha` | CharField(128) | Senha criptografada | Sim |
| `senha_plana` | CharField(20) | Senha em texto plano | Sim |
| `data_criacao` | DateTimeField | Data de criação | Auto |
| `enviado_whatsapp` | BooleanField | Enviado por WhatsApp | Não (default: False) |
| `data_envio_whatsapp` | DateTimeField | Data de envio | Não |

**Relações:**
- `ManyToOne` → `Academia` (via `academia`)
- `ManyToOne` → `Campeonato` (via `campeonato`)

**Constraints:**
- `unique_together`: (`academia`, `campeonato`)

**Métodos:**
- `verificar_senha(senha: str) -> bool`: Verifica senha usando SHA256
- `definir_senha(senha: str)`: Define senha com hash SHA256

**Lógica:**
- Senha gerada automaticamente ao criar campeonato
- Senha única por campeonato (não reutilizada)
- Senha plana armazenada temporariamente para envio via WhatsApp

---

## 2. Views

### 2.1 Autenticação

#### `login_operacional(request)`

**Descrição:** Login operacional usando autenticação Django.

**Fluxo:**
1. Verifica se já está autenticado → redireciona para dashboard
2. Verifica se está logado como academia → redireciona para painel academia
3. Se POST: valida usuário/senha via Django auth
4. Verifica perfil operacional (ativo, não expirado)
5. Cria perfil padrão se não existir (30 dias)
6. Faz login Django e redireciona para dashboard

**Dados Recebidos:**
- `POST['username']`: Nome de usuário
- `POST['password']`: Senha

**Dados Retornados:**
- Template: `login_operacional.html`
- Context: Mensagens de erro/sucesso

**Permissões:**
- Público (não autenticado)

---

#### `academia_login(request)`

**Descrição:** Login da academia usando sessão.

**Fluxo:**
1. Se POST: busca academia por login
2. Verifica senha geral ou senha do campeonato ativo
3. Se válido: cria sessão com `academia_id` e `academia_nome`
4. Redireciona para painel da academia

**Dados Recebidos:**
- `POST['login']`: Login da academia
- `POST['senha']`: Senha (geral ou do campeonato)

**Dados Retornados:**
- Template: `academia/login.html`
- Session: `academia_id`, `academia_nome`, `campeonato_id_ativo`

**Permissões:**
- Público (não autenticado)

---

#### `logout_geral(request)`

**Descrição:** Logout completo (academia e operacional).

**Fluxo:**
1. Remove `academia_id` e `academia_nome` da sessão
2. Faz logout Django se autenticado
3. Remove `operacional_logado` da sessão
4. Limpa toda a sessão e cookies
5. Redireciona para seleção de login

**Permissões:**
- Público

---

### 2.2 Dashboard e Navegação

#### `index(request)`

**Descrição:** Dashboard operacional principal.

**Fluxo:**
1. Verifica se logado como academia → redireciona
2. Verifica autenticação operacional → redireciona para login
3. Busca campeonato ativo
4. Calcula estatísticas (atletas, inscrições, chaves)
5. Busca ranking preview (top 5 academias)

**Dados Retornados:**
- Template: `index.html`
- Context: `campeonato_ativo`, `total_atletas`, `total_inscricoes`, `total_chaves`, `ranking_preview`

**Permissões:**
- `@operacional_required`

---

### 2.3 Gestão de Atletas

#### `cadastrar_atleta(request)`

**Descrição:** Cadastra novo atleta globalmente.

**Fluxo:**
1. Se POST: valida campos obrigatórios
2. Valida formato de data de nascimento
3. Calcula classe inicial baseada na idade
4. Valida número Zempo se federado
5. Salva atleta e foto/documento
6. Redireciona para lista de atletas

**Dados Recebidos:**
- `POST['nome']`, `POST['data_nascimento']`, `POST['sexo']`, `POST['academia']`
- `POST['federado']`, `POST['numero_zempo']`
- `FILES['foto_perfil']`, `FILES['documento_oficial']`

**Dados Retornados:**
- Template: `cadastrar_atleta.html`
- Context: `academias`, `old_data` (em caso de erro)

**Permissões:**
- `@operacional_required`

---

#### `editar_atleta(request, atleta_id)`

**Descrição:** Edita atleta existente.

**Fluxo:**
1. Busca atleta por ID
2. Se POST: atualiza campos
3. Recalcula classe se data de nascimento mudou
4. Atualiza foto/documento se fornecidos
5. Salva e redireciona

**Dados Recebidos:**
- Mesmos de `cadastrar_atleta`

**Dados Retornados:**
- Template: `editar_atleta.html`
- Context: `atleta`, `academias`

**Permissões:**
- `@operacional_required`

---

### 2.4 Pesagem

#### `pesagem(request)`

**Descrição:** Tela de pesagem (desktop).

**Fluxo:**
1. Busca campeonato ativo
2. Filtra inscrições aprovadas/confirmadas
3. Aplica filtros (nome, classe, categoria, academia)
4. Ordena por nome

**Dados Recebidos:**
- `GET['nome']`, `GET['classe']`, `GET['categoria']`, `GET['academia']`

**Dados Retornados:**
- Template: `pesagem.html`
- Context: `inscricoes`, `campeonato_ativo`, filtros

**Permissões:**
- `@operacional_required`

---

#### `registrar_peso(request, inscricao_id)`

**Descrição:** Registra peso oficial de uma inscrição.

**Fluxo:**
1. Busca inscrição por ID
2. Valida peso fornecido
3. Busca categoria escolhida
4. Verifica se peso está dentro dos limites
5. Se dentro: aprova inscrição
6. Se fora: sugere categoria adequada ou permite remanejamento
7. Salva peso e data de pesagem

**Dados Recebidos:**
- `POST['peso']`: Peso em kg
- `POST['categoria_ajustada']`: Categoria ajustada (opcional)
- `POST['motivo_ajuste']`: Motivo do ajuste (opcional)

**Dados Retornados:**
- JSON: `{'success': bool, 'message': str, 'categoria_sugerida': str}`

**Permissões:**
- `@operacional_required`

---

### 2.5 Chaves

#### `gerar_chave_view(request)`

**Descrição:** Gera chave automaticamente para uma categoria.

**Fluxo:**
1. Busca campeonato ativo
2. Se POST: busca inscrições aprovadas da categoria
3. Chama `gerar_chave()` de `utils.py`
4. Redireciona para detalhe da chave

**Dados Recebidos:**
- `POST['categoria']`, `POST['classe']`, `POST['sexo']`
- `POST['modelo_chave']`: Tipo de chave (opcional)

**Dados Retornados:**
- Redirect para `detalhe_chave`

**Permissões:**
- `@operacional_required`

---

#### `detalhe_chave(request, chave_id)`

**Descrição:** Exibe detalhes de uma chave.

**Fluxo:**
1. Busca chave por ID com `select_related('campeonato')`
2. Busca todas as lutas ordenadas por round
3. Enriquece lutas com informações de inscrições
4. Calcula resultados finais da chave

**Dados Retornados:**
- Template: `detalhe_chave.html`
- Context: `chave`, `lutas`, `resultados`, `campeonato`

**Permissões:**
- `@operacional_required`

---

### 2.6 Administração

#### `administracao_painel(request)`

**Descrição:** Dashboard administrativo (Visão Geral).

**Fluxo:**
1. Busca campeonato ativo
2. Calcula KPIs financeiros (entradas, despesas, lucro)
3. Calcula indicadores operacionais (equipe técnica)
4. Calcula indicadores estratégicos (ranking academias, top custos)
5. Prepara dados para gráficos

**Dados Retornados:**
- Template: `administracao/painel.html`
- Context: KPIs, indicadores financeiros, operacionais, estratégicos

**Permissões:**
- `@operacional_required`

---

#### `administracao_financeiro(request)`

**Descrição:** Painel financeiro detalhado.

**Fluxo:**
1. Busca campeonato ativo
2. Calcula entradas (previstas, caixa, pendentes)
3. Calcula despesas (total, pagas, pendentes)
4. Calcula bônus de professores
5. Calcula saldo final

**Dados Retornados:**
- Template: `administracao/financeiro.html`
- Context: Valores financeiros, despesas recentes

**Permissões:**
- `@operacional_required`

---

### 2.7 Módulo Academia

#### `academia_painel(request)`

**Descrição:** Painel principal da academia.

**Fluxo:**
1. Busca academia da sessão
2. Busca todos os campeonatos
3. Filtra campeonatos abertos ou que a academia participa
4. Calcula estatísticas por campeonato

**Dados Retornados:**
- Template: `academia/painel.html`
- Context: `academia`, `eventos_disponiveis`, `eventos_participando`

**Permissões:**
- `@academia_required`

---

#### `academia_inscrever_atletas(request, campeonato_id)`

**Descrição:** Tela de inscrição de atletas da academia.

**Fluxo:**
1. Busca academia da sessão e campeonato
2. Busca atletas da academia
3. Se POST: cria inscrição
4. Valida elegibilidade de categoria
5. Salva inscrição com status 'pendente'

**Dados Recebidos:**
- `POST['atleta']`, `POST['classe_escolhida']`, `POST['categoria_escolhida']`

**Dados Retornados:**
- Template: `academia/inscrever_atletas.html`
- Context: `academia`, `campeonato`, `atletas`, `inscricoes`

**Permissões:**
- `@academia_required`

---

## 3. URLs

### Tabela Completa de Rotas

| Rota | View | Nome | Parâmetros | Permissões |
|------|------|------|------------|------------|
| `/` | `selecionar_tipo_login` | `root` | - | Público |
| `/dashboard/` | `index` | `index` | - | Operacional |
| `/academias/` | `lista_academias` | `lista_academias` | - | Operacional |
| `/academias/cadastrar/` | `cadastrar_academia` | `cadastrar_academia` | - | Operacional |
| `/academias/<id>/` | `detalhe_academia` | `detalhe_academia` | `academia_id` | Operacional |
| `/academias/<id>/editar/` | `editar_academia` | `editar_academia` | `academia_id` | Operacional |
| `/categorias/` | `lista_categorias` | `lista_categorias` | - | Operacional |
| `/categorias/cadastrar/` | `cadastrar_categoria` | `cadastrar_categoria` | - | Operacional |
| `/atletas/` | `lista_atletas` | `lista_atletas` | - | Operacional |
| `/atletas/cadastrar/` | `cadastrar_atleta` | `cadastrar_atleta` | - | Operacional |
| `/atletas/<id>/editar/` | `editar_atleta` | `editar_atleta` | `atleta_id` | Operacional |
| `/atletas/<id>/perfil/` | `perfil_atleta` | `perfil_atleta` | `atleta_id` | Operacional |
| `/atletas/importar/` | `importar_atletas` | `importar_atletas` | - | Operacional |
| `/pesagem/` | `pesagem` | `pesagem` | - | Operacional |
| `/pesagem/mobile/` | `pesagem_mobile_view` | `pesagem_mobile` | - | Operacional |
| `/pesagem/inscricao/<id>/registrar/` | `registrar_peso` | `registrar_peso` | `inscricao_id` | Operacional |
| `/chaves/` | `lista_chaves` | `lista_chaves` | - | Operacional |
| `/chaves/gerar/` | `gerar_chave_view` | `gerar_chave_view` | - | Operacional |
| `/chaves/gerar-manual/` | `gerar_chave_manual` | `gerar_chave_manual` | - | Operacional |
| `/chaves/<id>/` | `detalhe_chave` | `detalhe_chave` | `chave_id` | Operacional |
| `/chaves/<id>/imprimir/` | `imprimir_chave` | `imprimir_chave` | `chave_id` | Operacional |
| `/lutas/<id>/registrar-vencedor/` | `registrar_vencedor` | `registrar_vencedor` | `luta_id` | Operacional |
| `/ranking/` | `ranking_academias` | `ranking_academias` | - | Operacional |
| `/ranking/global/` | `ranking_global` | `ranking_global` | - | Operacional |
| `/ranking/calcular/` | `calcular_pontuacao` | `calcular_pontuacao` | - | Operacional |
| `/inscricoes/` | `inscrever_atletas` | `inscrever_atletas` | - | Operacional |
| `/metricas/` | `metricas_evento` | `metricas_evento` | - | Operacional |
| `/campeonatos/` | `lista_campeonatos` | `lista_campeonatos` | - | Operacional |
| `/campeonatos/cadastrar/` | `cadastrar_campeonato` | `cadastrar_campeonato` | - | Operacional |
| `/campeonatos/<id>/editar/` | `editar_campeonato` | `editar_campeonato` | `campeonato_id` | Operacional |
| `/campeonatos/<id>/ativar/` | `definir_campeonato_ativo` | `definir_campeonato_ativo` | `campeonato_id` | Operacional |
| `/campeonatos/<id>/senhas/` | `gerenciar_senhas_campeonato` | `gerenciar_senhas_campeonato` | `campeonato_id` | Operacional |
| `/login/` | `selecionar_tipo_login` | `selecionar_tipo_login` | - | Público |
| `/login/operacional/` | `login_operacional` | `login_operacional` | - | Público |
| `/logout/` | `logout_geral` | `logout_geral` | - | Público |
| `/academia/login/` | `academia_login` | `academia_login` | - | Público |
| `/academia/` | `academia_painel` | `academia_painel` | - | Academia |
| `/academia/evento/<id>/` | `academia_evento` | `academia_evento` | `campeonato_id` | Academia |
| `/academia/inscrever/<id>/` | `academia_inscrever_atletas` | `academia_inscrever_atletas` | `campeonato_id` | Academia |
| `/academia/atleta/novo/` | `academia_cadastrar_atleta` | `academia_cadastrar_atleta` | - | Academia |
| `/academia/chaves/<id>/` | `academia_ver_chaves` | `academia_ver_chaves` | `campeonato_id` | Academia |
| `/academia/chave/<id>/<id>/` | `academia_detalhe_chave` | `academia_detalhe_chave` | `campeonato_id`, `chave_id` | Academia |
| `/administracao/` | `administracao_painel` | `administracao_painel` | - | Operacional |
| `/administracao/financeiro/` | `administracao_financeiro` | `administracao_financeiro` | - | Operacional |
| `/administracao/financeiro/despesas/` | `administracao_despesas` | `administracao_despesas` | - | Operacional |
| `/administracao/equipe/` | `administracao_equipe` | `administracao_equipe` | - | Operacional |
| `/administracao/insumos/` | `administracao_insumos` | `administracao_insumos` | - | Operacional |
| `/administracao/patrocinios/` | `administracao_patrocinios` | `administracao_patrocinios` | - | Operacional |
| `/administracao/relatorios/` | `administracao_relatorios` | `administracao_relatorios` | - | Operacional |
| `/administracao/banco-operacional/<tipo>/` | `administracao_cadastros_operacionais` | `administracao_cadastros_operacionais` | `tipo` | Operacional |
| `/administracao/usuarios-operacionais/` | `gerenciar_usuarios_operacionais` | `gerenciar_usuarios_operacionais` | - | Pode Criar Usuários |
| `/administracao/conferencia-inscricoes/` | `administracao_conferencia_inscricoes` | `administracao_conferencia_inscricoes` | - | Operacional |
| `/api/admin/reset/` | `ResetCompeticaoAPIView` | `reset_campeonato` | - | Pode Resetar |

---

## 4. Templates

### 4.1 Estrutura e Blocos

#### Template Base: `base.html`

**Estrutura:**
```html
{% load static %}
<!DOCTYPE html>
<html>
<head>
    {% block title %}{% endblock %}
    <style>/* Design System CSS */</style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="sidebar">{% block sidebar %}{% endblock %}</div>
    <div class="navbar">{% block navbar %}{% endblock %}</div>
    <div class="main-content">
        <div class="content-wrapper">
            {% block content %}{% endblock %}
        </div>
    </div>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Blocos Disponíveis:**
- `title`: Título da página
- `extra_css`: CSS adicional
- `sidebar`: Menu lateral
- `navbar`: Barra superior
- `content`: Conteúdo principal
- `extra_js`: JavaScript adicional

---

#### Template Academia: `academia/base_academia.html`

**Estrutura:**
- Template independente para módulo de academias
- Não usa sidebar/navbar do sistema operacional
- Design simplificado e mobile-first

---

### 4.2 Componentes Reutilizáveis

#### `partials/kpi_card.html`

**Uso:**
```django
{% include 'atletas/administracao/partials/kpi_card.html' with 
    label='Inscrições Pendentes' 
    value='42' 
    icon_path='M12 4v16m8-8H4' 
    icon_bg='var(--color-primary-light)'
    icon_color='var(--color-primary)'
    change_text='+5 desde ontem'
    change_positive=True
%}
```

**Parâmetros:**
- `label`: Título do KPI
- `value`: Valor principal
- `icon_path`: Path do SVG
- `icon_bg`: Cor de fundo do ícone
- `icon_color`: Cor do ícone
- `change_text`: Texto de mudança (opcional)
- `change_positive/negative`: Indicador de tendência

---

#### `partials/operacional_card.html`

**Uso:**
```django
{% include 'atletas/administracao/partials/operacional_card.html' with 
    titulo='Árbitros' 
    count=15 
    url='arbitro' 
    icon='M12 4v16m8-8H4'
%}
```

**Parâmetros:**
- `titulo`: Título do card
- `count`: Quantidade de registros
- `url`: Tipo de cadastro operacional
- `icon`: Path do SVG

---

#### `partials/section_header.html`

**Uso:**
```django
{% include 'atletas/administracao/partials/section_header.html' with 
    titulo='Despesas Recentes' 
    acao_url='administracao_despesas' 
    acao_texto='Gerenciar Despesas'
    acao_icone='M11 4H4a2...'
%}
```

---

### 4.3 Layout Padrão

**Estrutura de Página:**
```html
<div class="page-header">
    <h1 class="page-title">Título da Página</h1>
    <p class="page-description">Descrição</p>
</div>

<div class="main-content-grid">
    <div class="card">
        <div class="card-header">
            <h2 class="card-title">Seção</h2>
        </div>
        <div class="card-body">
            <!-- Conteúdo -->
        </div>
    </div>
</div>
```

**Classes Utilitárias:**
- `.flex`, `.flex-col`, `.items-center`, `.justify-between`
- `.grid`, `.grid-auto-fit`, `.grid-2`, `.grid-3`
- `.p-4`, `.p-6`, `.mb-4`, `.mt-6`
- `.text-sm`, `.text-lg`, `.font-semibold`
- `.text-gray-500`, `.text-primary`, `.text-danger`

---

## 5. Lógica de Negócio

### 5.1 Inscrições

**Fluxo:**
1. Atleta selecionado ou cadastrado
2. Sistema calcula classe baseada em `data_nascimento`
3. Sistema lista categorias elegíveis para a classe
4. Usuário escolhe categoria
5. Sistema valida elegibilidade via `validar_elegibilidade_categoria()`
6. Inscrição criada com status `pendente`
7. Organizador confirma → status `confirmado` (conta para caixa)
8. Após pesagem → status `aprovado` (pode gerar chave)

**Regras de Elegibilidade:**
- **VETERANOS**: Pode escolher VETERANOS ou SÊNIOR
- **SUB 18**: Pode escolher SUB 18, SUB 21 (se existir) ou SÊNIOR
- **Demais classes**: Apenas sua própria classe

**Validações:**
- Atleta deve ter documento oficial (para inscrição)
- Atleta federado deve ter número Zempo
- Não pode inscrever na mesma classe/categoria duas vezes

---

### 5.2 Pesagem

**Fluxo:**
1. Inscrição com status `confirmado` ou `aprovado`
2. Peso oficial registrado
3. Sistema busca categoria escolhida
4. Verifica se peso está dentro dos limites:
   - **Dentro**: Status `aprovado`, categoria mantida
   - **Acima do limite**: Sugere categoria inferior ou elimina
   - **Abaixo do limite**: Pode subir categoria (se permitido)
5. Se remanejado: `categoria_ajustada` preenchida, `remanejado = True`
6. `data_pesagem` registrada

**Ajuste de Categoria:**
- Sistema busca categoria adequada baseada no peso
- Organizador pode aprovar remanejamento ou rebaixar
- Motivo do ajuste registrado em `motivo_ajuste`

---

### 5.3 Chaves

**Geração Automática:**

1. Sistema busca inscrições com status `aprovado` da categoria
2. Filtra por `classe_escolhida`, `sexo` e `categoria` (escolhida ou ajustada)
3. Determina tipo de chave baseado no número de atletas:
   - **0**: Chave vazia
   - **1**: Campeão automático
   - **2**: Melhor de 3
   - **3**: Triangular
   - **4**: Olímpica 4
   - **5-8**: Olímpica 8
   - **9-16**: Olímpica 16
   - **17-32**: Olímpica 32
   - **33+**: Round Robin
4. Distribui atletas na chave
5. Cria todas as lutas necessárias
6. Define estrutura de avanço (`proxima_luta`)

**Modelos de Chave Selecionáveis:**

- `vazia`: Nenhuma luta
- `campeao_automatico`: 1 atleta
- `melhor_de_3`: 2 atletas
- `triangular`: 3 atletas
- `olimpica_4`: 4 atletas
- `olimpica_8`: 8 atletas
- `olimpica_16`: 16 atletas
- `olimpica_32`: 32 atletas
- `round_robin`: Todos contra todos

**Registro de Resultados:**

1. Vencedor registrado em cada luta
2. Tipo de vitória registrado (Ippon, Wazari, Yuko)
3. Sistema atualiza `proxima_luta` automaticamente
4. Vencedor avança para próxima fase
5. Ao finalizar todas as lutas: pódio calculado automaticamente

---

### 5.4 Ranking

**Cálculo de Pontuação:**

- **1º Lugar (Ouro)**: 10 pontos
- **2º Lugar (Prata)**: 7 pontos
- **3º Lugar (Bronze)**: 5 pontos (cada)
- **4º Lugar**: 3 pontos
- **5º Lugar**: 1 ponto

**Processo:**

1. Ao finalizar cada chave, sistema calcula pódio
2. Atribui medalhas à academia do atleta
3. Soma pontos em `AcademiaPontuacao`
4. Ranking atualizado automaticamente

**Ranking Global vs. Evento:**

- **Ranking do Evento**: Apenas pontuações do campeonato ativo
- **Ranking Global**: Soma de todas as pontuações de todos os eventos

---

### 5.5 Lógica Financeira

**Entradas:**

- **Ganho Previsto**: `SUM(valor × (inscrições pendentes + confirmadas))`
- **Dinheiro em Caixa**: `SUM(valor × inscrições confirmadas)`
- **Pagamentos Pendentes**: `SUM(valor × inscrições pendentes)`

**Despesas:**

- Categorizadas por tipo (árbitros, mesários, etc.)
- Status: `pago` ou `pendente`
- Total calculado por categoria e status

**Bônus de Professores:**

- **Percentual**: `bonus_percentual × valor_total_inscricoes_confirmadas / 100`
- **Fixo**: `bonus_fixo × quantidade_atletas_confirmados`
- Calculado por academia

**Saldo Final:**

```
Saldo = (Dinheiro em Caixa) - (Despesas Pagas) - (Total Bônus)
```

---

### 5.6 Lógica da Academia

**Isolamento de Dados:**

- Academia só vê seus próprios atletas
- Academia só vê suas próprias inscrições
- Academia só vê chaves com seus atletas
- Não tem acesso a dados financeiros ou operacionais

**Ações Permitidas:**

- Inscrever atletas no campeonato
- Cadastrar novos atletas (vinculados à academia)
- Visualizar chaves (somente leitura)
- Baixar regulamento do campeonato

**Ações Bloqueadas:**

- Modificar chaves ou resultados
- Ver dados de outras academias
- Acessar módulo administrativo
- Resetar campeonato

---

### 5.7 Regras de Acesso

#### Operacional

**Autenticação:**
- Django `User` model
- Decorator `@operacional_required`
- Verifica `request.user.is_authenticated`
- Verifica perfil `UsuarioOperacional` (ativo, não expirado)

**Permissões Granulares:**
- `pode_resetar_campeonato`: Apenas usuário principal
- `pode_criar_usuarios`: Apenas usuário principal
- Validade: 30 dias (padrão) ou vitalício

**Acesso:**
- Todas as funcionalidades do sistema
- Módulo administrativo completo
- Reset de campeonato (se permitido)

---

#### Academia

**Autenticação:**
- Sessão Django (`request.session['academia_id']`)
- Decorator `@academia_required`
- Verifica `Academia.ativo_login = True`
- Senha: geral ou do campeonato ativo

**Acesso:**
- Painel da academia
- Inscrição de atletas
- Visualização de chaves (somente leitura)
- Lista de atletas da academia

**Restrições:**
- Não pode acessar módulo operacional
- Não pode modificar dados de outras academias
- Não pode acessar dados financeiros

---

## 6. Segurança

### 6.1 Permissões

#### Decorators de Autenticação

**`@operacional_required`**
- Verifica autenticação Django
- Verifica perfil operacional ativo
- Verifica expiração do acesso
- Redireciona para login se não autenticado

**`@academia_required`**
- Verifica sessão `academia_id`
- Verifica `Academia.ativo_login`
- Redireciona para seleção de login se não autenticado

**`@pode_resetar_required`**
- Requer `@operacional_required`
- Verifica `perfil.pode_resetar_campeonato = True`
- Apenas usuário principal tem esta permissão

**`@pode_criar_usuarios_required`**
- Requer `@operacional_required`
- Verifica `perfil.pode_criar_usuarios = True`
- Apenas usuário principal tem esta permissão

---

### 6.2 Proteção de Dados

**Isolamento de Sessão:**
- Academia não acessa dados de outras academias
- Filtros automáticos por `academia_id` na sessão
- Validação de propriedade em todas as ações

**Validação de Propriedade:**
- Academia só pode inscrever seus próprios atletas
- Academia só pode cadastrar atletas vinculados a ela
- Validação em todas as views do módulo academia

**Proteção CSRF:**
- Todos os formulários usam `{% csrf_token %}`
- Middleware CSRF ativo por padrão no Django

---

### 6.3 Senhas para Academia

**Geração Automática:**

1. Ao criar campeonato, sistema gera senha única para cada academia
2. Senha gerada: 8 caracteres alfanuméricos aleatórios
3. Senha armazenada em `AcademiaCampeonatoSenha`
4. Hash SHA256 armazenado em `senha`
5. Senha plana armazenada temporariamente em `senha_plana`

**Envio via WhatsApp:**

1. Sistema monta mensagem com credenciais
2. Link para login incluído na mensagem
3. Botão "Enviar por WhatsApp" abre WhatsApp Web/App
4. Mensagem pré-formatada com dados do campeonato

**Validação no Login:**

1. Sistema tenta senha geral primeiro (`Academia.senha_login`)
2. Se falhar, tenta senha do campeonato ativo
3. Se válida, marca `enviado_whatsapp = True`

**Reenvio:**

- Organizador pode reenviar senha a qualquer momento
- Senha não é regenerada (mantém a mesma)
- Histórico de envio registrado em `data_envio_whatsapp`

---

### 6.4 Login Operacional Exclusivo

**Criação do Usuário Principal:**

```bash
python3 manage.py criar_usuario_principal --username vinicius --password V1n1c1u5@#
```

**Características:**
- Usuário criado como `superuser` do Django
- Perfil `UsuarioOperacional` criado com:
  - `pode_resetar_campeonato = True`
  - `pode_criar_usuarios = True`
  - `data_expiracao = None` (vitalício)
  - `ativo = True`

**Segurança:**
- Apenas este usuário pode resetar campeonato
- Apenas este usuário pode criar outros usuários operacionais
- Senha deve ser forte e guardada com segurança

**Criação de Usuários Secundários:**

1. Apenas usuário principal pode criar
2. Usuários criados têm validade de 30 dias (padrão)
3. Permissões limitadas (não podem resetar nem criar usuários)
4. Criador registrado em `criado_por`

---

### 6.5 Hash de Senhas

**Algoritmo:**
- SHA256 (simples, adequado para este contexto)
- Em produção, considerar bcrypt ou Argon2

**Implementação:**
```python
import hashlib
senha_hash = hashlib.sha256(senha.encode()).hexdigest()
```

**Armazenamento:**
- Senha nunca armazenada em texto plano (exceto temporariamente para envio)
- Hash comparado na validação
- Senha plana removida após envio (opcional)

---

## 📝 Notas Finais

Esta documentação cobre a estrutura técnica completa do sistema SHIAI. Para detalhes de implementação específicos, consulte o código-fonte e os comentários inline.

**Última Atualização:** 2024  
**Versão do Sistema:** 1.0

