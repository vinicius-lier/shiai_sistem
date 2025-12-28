<<<<<<< HEAD
# 🥋 SHIAI SISTEM - Sistema de Gestão de Competições de Judô

[![Django](https://img.shields.io/badge/Django-5.2.8-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat)](LICENSE)

---

## 📋 Índice

1. [Introdução](#introdução)
2. [Tecnologias](#tecnologias)
3. [Instalação](#instalação)
4. [Estrutura do Projeto](#estrutura-do-projeto)
5. [Lógica de Funcionamento](#lógica-de-funcionamento)
6. [Boas Práticas](#boas-práticas)
7. [Créditos](#créditos)

---

## 🎯 Introdução

### O que é o SHIAI

O **SHIAI SISTEM** é uma plataforma web completa e profissional para gestão de competições de Judô, desenvolvida especificamente para substituir sistemas baseados em planilhas Excel e automatizar todo o fluxo de uma competição, desde as inscrições até a geração de relatórios finais.

O sistema foi projetado para ser **intuitivo**, **confiável** e **eficiente**, oferecendo uma experiência moderna tanto para organizadores quanto para academias participantes.

### Principais Objetivos

- ✅ **Automatizar** todo o processo de gestão de competições de Judô
- ✅ **Centralizar** informações de atletas, academias e eventos
- ✅ **Facilitar** inscrições e gestão de participantes
- ✅ **Otimizar** a pesagem e ajuste automático de categorias
- ✅ **Gerar** chaves de competição automaticamente
- ✅ **Calcular** pontuação e rankings em tempo real
- ✅ **Fornecer** relatórios e métricas detalhadas
- ✅ **Gerenciar** aspectos financeiros e operacionais do evento

### Quem Utiliza

- **Organizadores de Competições**: Gestão completa do evento
- **Academias**: Inscrição de atletas e acompanhamento de resultados
- **Equipe Operacional**: Registro de pesagem, resultados e controle de chaves
- **Administradores**: Visão geral financeira e operacional

### Controle de Acesso

- Controle de acesso baseado em role (`ADMIN`/`STAFF`), não em `auth_permission`.

---

## 🛠️ Tecnologias

### Backend

- **Django 5.2.8**: Framework web Python de alto nível
- **Python 3.10+**: Linguagem de programação
- **Django REST Framework**: API REST para integrações
- **SQLite**: Banco de dados padrão (pode ser migrado para PostgreSQL/MySQL em produção)

### Frontend

- **HTML5**: Estrutura semântica
- **CSS3**: Design System customizado (variáveis CSS, mobile-first)
- **JavaScript (Vanilla)**: Interatividade e validações client-side
- **SVG Icons**: Heroicons/Feather Icons para interface

### Design System

O sistema utiliza um **Design System próprio** definido em `base.html` com:

- **Cores**: Paleta SHIAI (azul primário, roxo secundário, tons de cinza)
- **Tipografia**: Fonte Inter (Google Fonts)
- **Espaçamento**: Sistema de 8px (grid system)
- **Componentes**: Cards, botões, formulários, tabelas padronizados
- **Responsividade**: Mobile-first, adaptável para tablets e desktop

### Estrutura das Apps

```
judocomp/              # Projeto Django principal
├── settings.py        # Configurações do projeto
├── urls.py            # URLs principais
└── wsgi.py            # WSGI config

atletas/               # App principal
├── models.py          # Modelos de dados (Academia, Atleta, Chave, etc.)
├── views.py           # Views e lógica de negócio
├── urls.py            # Rotas da aplicação
├── utils.py           # Funções utilitárias (cálculos, geração de chaves)
├── constants.py       # Constantes e mensagens padronizadas
├── academia_auth.py   # Decorators de autenticação
├── templates/         # Templates HTML
│   ├── base.html      # Template base com Design System
│   ├── administracao/ # Módulo administrativo
│   ├── academia/      # Módulo de academias
│   └── relatorios/    # Relatórios
└── management/        # Comandos Django customizados
    └── commands/       # Scripts de manutenção
```

---

## 🚀 Instalação

### Requisitos

- **Python 3.10+**
- **pip** (gerenciador de pacotes Python)
- **Git** (opcional, para clonar o repositório)

### Passo a Passo

#### 1. Clonar ou Baixar o Projeto

```bash
# Se usar Git
git clone <url-do-repositorio>
cd shiai_sistem-main

# Ou extraia o arquivo ZIP na pasta desejada
```

#### 2. Criar Ambiente Virtual (Recomendado)

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- Django>=5.2.8,<6.0
- djangorestframework (para APIs)

#### 4. Configurar Banco de Dados

```bash
# Aplicar migrações
python3 manage.py migrate
```

O sistema utiliza **SQLite** por padrão (arquivo `db.sqlite3`). Para produção, recomenda-se migrar para PostgreSQL ou MySQL.

#### 5. Criar Usuário Operacional Principal

```bash
# Criar usuário principal com permissões totais
python3 manage.py criar_usuario_principal --username vinicius --password V1n1c1u5@#
```

Este comando cria o usuário operacional principal com:
- Acesso vitalício
- Permissão para resetar campeonatos
- Permissão para criar outros usuários operacionais

#### 6. Executar Servidor de Desenvolvimento

```bash
# Servidor local (localhost)
python3 manage.py runserver

# Servidor acessível na rede local
python3 manage.py runserver 0.0.0.0:8000
```

#### 7. Acessar o Sistema

- **Local**: http://127.0.0.1:8000/
- **Rede Local**: http://[IP-DO-SERVIDOR]:8000/

---

## 📁 Estrutura do Projeto

### Módulo Global

Funcionalidades disponíveis independentemente do campeonato ativo:

#### **Atletas**
- Cadastro global de atletas (não vinculado a evento específico)
- Gestão de informações pessoais, documentos e fotos
- Histórico de participações
- **Rota**: `/atletas/`

#### **Academias**
- Cadastro de academias participantes
- Informações de contato e responsáveis
- Sistema de login para academias
- Bônus de professores (percentual ou fixo)
- **Rota**: `/academias/`

#### **Ranking Global**
- Ranking consolidado de todas as academias
- Histórico de pontuações em todos os eventos
- **Rota**: `/ranking/global/`

#### **Campeonatos**
- Criação e gestão de múltiplos campeonatos
- Definição de campeonato ativo
- Configuração de valores de inscrição
- Geração automática de senhas por campeonato
- **Rota**: `/campeonatos/`

### Módulo de Evento Ativo

Funcionalidades vinculadas ao campeonato ativo:

#### **Inscrições**
- Inscrição de atletas no campeonato ativo
- Seleção de classe e categoria
- Status de inscrição (Pendente, Confirmado, Aprovado)
- **Rota**: `/inscricoes/`

#### **Categorias**
- Gestão de categorias oficiais
- Definição de limites de peso por categoria
- **Rota**: `/categorias/`

#### **Pesagem**
- Registro de peso oficial dos atletas
- Ajuste automático de categoria por peso
- Remanejamento de categoria quando necessário
- Aprovação/reprovação na pesagem
- **Rota**: `/pesagem/` (desktop) e `/pesagem/mobile/` (mobile)

#### **Chaves**
- Geração automática de chaves por categoria
- Tipos de chave: Olímpica, Triangular, Melhor de 3, Round Robin
- Visualização detalhada de cada chave
- Impressão de chaves em formato A4
- **Rota**: `/chaves/`

#### **Ranking do Evento**
- Ranking das academias no campeonato ativo
- Pontuação por medalhas (Ouro, Prata, Bronze)
- **Rota**: `/ranking/`

#### **Métricas**
- Dashboard com métricas do evento
- Estatísticas de inscrições, pesagem e resultados
- **Rota**: `/metricas/`

### Módulo de Administração

Painel administrativo completo para gestão do evento:

#### **Visão Geral**
- Dashboard executivo com KPIs principais
- Indicadores financeiros, operacionais e estratégicos
- Gráficos e visualizações de dados
- **Rota**: `/administracao/`

#### **Financeiro**
- Controle de entradas (inscrições confirmadas)
- Gestão de despesas por categoria
- Cálculo de bônus de professores
- Saldo final (lucro/prejuízo)
- **Rota**: `/administracao/financeiro/`

#### **Equipe Técnica**
- CRUD de árbitros, mesários, oficiais
- Gestão de coordenadores e oficiais de pesagem
- Envio de convites via WhatsApp
- **Rota**: `/administracao/equipe/`

#### **Banco Operacional**
- Cadastro de recursos operacionais
- Ambulâncias, insumos, estrutura
- Patrocínios (entradas)
- **Rota**: `/administracao/banco-operacional/<tipo>/`

#### **Relatórios**
- Exportação de relatórios em PDF
- Relatórios financeiros, de equipe e estrutura
- **Rota**: `/administracao/relatorios/`

#### **Resetar Campeonato**
- Reset completo do campeonato ativo
- Limpeza de chaves, lutas e pontuações
- Requer permissão especial e confirmação por senha
- **Rota**: API `/api/admin/reset/`

### Módulo de Academia

Painel exclusivo para academias participantes:

#### **Login da Academia**
- Login independente do sistema operacional
- Senha única por campeonato
- Envio automático de credenciais via WhatsApp
- **Rota**: `/academia/login/`

#### **Painel da Academia**
- Lista de eventos disponíveis
- Eventos em que a academia participa
- **Rota**: `/academia/painel/`

#### **Gestão de Atletas no Evento**
- Inscrição de atletas no campeonato
- Cadastro de novos atletas
- Lista de atletas inscritos com status
- **Rota**: `/academia/evento/<id>/`

#### **Visualização de Chaves**
- Visualização de chaves em modo somente leitura
- Acompanhamento de progresso das lutas
- Download de PDFs das chaves
- **Rota**: `/academia/chaves/<campeonato_id>/`

---

## ⚙️ Lógica de Funcionamento

### Pesagem

1. **Registro de Peso**: O peso oficial é registrado na tela de pesagem
2. **Validação Automática**: Sistema verifica se o peso está dentro dos limites da categoria escolhida
3. **Ajuste de Categoria**: Se necessário, o sistema sugere categoria adequada
4. **Remanejamento**: Organizador pode aprovar remanejamento ou rebaixar categoria
5. **Status Final**: Atleta pode ser aprovado ou reprovado na pesagem

**Regras de Ajuste:**
- Se peso está dentro dos limites: **Status OK**
- Se peso excede limite: **Pode rebaixar** ou **Eliminado**
- Se peso está abaixo: **Pode subir** de categoria (se permitido)

### Inscrições

1. **Seleção de Atleta**: Escolha de atleta cadastrado ou cadastro de novo
2. **Seleção de Classe**: Sistema calcula classe baseada na data de nascimento
3. **Seleção de Categoria**: Lista apenas categorias elegíveis para a classe
4. **Validação de Elegibilidade**: Sistema valida se atleta pode competir na categoria escolhida
5. **Status da Inscrição**:
   - **Pendente**: Aguardando confirmação do organizador
   - **Confirmado**: Confirmado pelo organizador (conta para caixa)
   - **Aprovado**: Aprovado para gerar chave (após pesagem)

**Regras de Elegibilidade:**
- **SUB 18**: Pode competir em SUB 18, SUB 21, SÊNIOR
- **SUB 21**: Pode competir em SUB 21, SÊNIOR
- **SÊNIOR**: Pode competir apenas em SÊNIOR
- **VETERANOS**: Pode competir apenas em VETERANOS

### Chaves

O sistema gera automaticamente o tipo de chave baseado no número de atletas:

| Nº Atletas | Tipo de Chave | Descrição |
|------------|---------------|-----------|
| 0 | Vazia | Nenhuma luta criada |
| 1 | Campeão Automático | Atleta vence automaticamente |
| 2 | Melhor de 3 | Primeiro a vencer 2 lutas |
| 3 | Triangular | Todos contra todos (3 lutas) |
| 4 | Olímpica 4 | Chave eliminatória de 4 |
| 5-8 | Olímpica 8 | Chave eliminatória de 8 |
| 9-16 | Olímpica 16 | Chave eliminatória de 16 |
| 17-32 | Olímpica 32 | Chave eliminatória de 32 |
| 33+ | Round Robin | Todos contra todos |

**Geração Automática:**
- Sistema distribui atletas automaticamente na chave
- Cria todas as lutas necessárias
- Define estrutura de avanço (próxima luta)

**Registro de Resultados:**
- Cada luta registra vencedor e tipo de vitória (Ippon, Wazari, Yuko)
- Sistema atualiza automaticamente a próxima luta
- Pódio é calculado automaticamente ao finalizar todas as lutas

### Ranking

**Sistema de Pontuação:**
- **1º Lugar (Ouro)**: 10 pontos
- **2º Lugar (Prata)**: 7 pontos
- **3º Lugar (Bronze)**: 5 pontos (cada)
- **4º Lugar**: 3 pontos
- **5º Lugar**: 1 ponto

**Cálculo:**
- Pontos são atribuídos automaticamente ao finalizar cada chave
- Sistema soma pontos por academia
- Ranking é atualizado em tempo real

**Ranking Global vs. Ranking do Evento:**
- **Ranking do Evento**: Pontuação apenas do campeonato ativo
- **Ranking Global**: Soma de pontuações de todos os eventos

### Regras SUB18/SUB21/Sênior/Veteranos

O sistema implementa as regras oficiais de elegibilidade:

**SUB 18 (até 18 anos):**
- Pode competir em: SUB 18, SUB 21, SÊNIOR
- Cálculo baseado no ano de nascimento

**SUB 21 (até 21 anos):**
- Pode competir em: SUB 21, SÊNIOR
- Não pode competir em SUB 18

**SÊNIOR:**
- Pode competir apenas em SÊNIOR
- Idade acima de 21 anos

**VETERANOS:**
- Categoria exclusiva para atletas veteranos
- Não pode competir em outras categorias

### Financeiro

**Entradas:**
- **Estimado**: Soma de (valor × inscrições pendentes + confirmadas)
- **Caixa**: Soma de (valor × inscrições confirmadas)
- Valores diferenciados para federados e não federados

**Despesas:**
- Categorias: Árbitros, Mesários, Coordenadores, Insumos, etc.
- Status: Pendente ou Pago
- Controle de pagamentos e observações

**Bônus de Professores:**
- Percentual sobre inscrições confirmadas
- Ou valor fixo por atleta confirmado
- Cálculo automático no painel financeiro

**Saldo Final:**
- **Lucro/Prejuízo** = (Caixa) - (Despesas Pagas) - (Bônus)

### Lógica da Academia x Operacional

O sistema possui **dois tipos de login** completamente independentes:

#### **Login Operacional**
- Acesso ao sistema completo de gestão
- Usuários criados pelo administrador principal
- Permissões granulares (resetar campeonato, criar usuários)
- Validade configurável (30 dias padrão ou vitalício)

#### **Login da Academia**
- Acesso restrito ao painel da academia
- Senha única por campeonato
- Visualização apenas de:
  - Eventos disponíveis
  - Atletas da própria academia
  - Chaves com atletas da academia
  - Status de inscrições
- Ações permitidas:
  - Inscrever atletas
  - Cadastrar novos atletas
  - Visualizar chaves (somente leitura)

**Isolamento de Dados:**
- Academias só veem seus próprios atletas
- Não têm acesso a dados financeiros ou operacionais
- Não podem modificar chaves ou resultados

---

## 📚 Boas Práticas

### Como Contribuir

1. **Fork** o repositório (se aplicável)
2. Crie uma **branch** para sua feature: `git checkout -b feature/nova-funcionalidade`
3. **Commit** suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. **Push** para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um **Pull Request**

### Padrões de Código

- **Python**: Seguir PEP 8
- **Django**: Seguir boas práticas do Django
- **Templates**: Usar classes utilitárias do Design System
- **CSS**: Evitar estilos inline, preferir classes do sistema
- **JavaScript**: Código vanilla, sem dependências externas

### Como Registrar Issues

Ao reportar um problema ou sugerir uma melhoria:

1. **Título claro** e descritivo
2. **Descrição detalhada** do problema
3. **Passos para reproduzir** (se for bug)
4. **Comportamento esperado** vs. **comportamento atual**
5. **Screenshots** (se aplicável)
6. **Ambiente**: Versão do Python, Django, SO

**Template de Issue:**

```markdown
**Descrição:**
[Descreva o problema ou sugestão]

**Passos para Reproduzir:**
1. 
2. 
3. 

**Comportamento Esperado:**
[O que deveria acontecer]

**Comportamento Atual:**
[O que está acontecendo]

**Ambiente:**
- Python: [versão]
- Django: [versão]
- SO: [sistema operacional]
```

### Comandos Úteis

```bash
# Criar migrações
python3 manage.py makemigrations

# Aplicar migrações
python3 manage.py migrate

# Criar superusuário Django
python3 manage.py createsuperuser

# Criar usuário operacional principal
python3 manage.py criar_usuario_principal

# Coletar arquivos estáticos (produção)
python3 manage.py collectstatic

# Shell do Django (para testes)
python3 manage.py shell
```

### Estrutura de Desenvolvimento

1. **Desenvolvimento Local**: Use `runserver` para desenvolvimento
2. **Testes**: Teste todas as funcionalidades antes de commitar
3. **Migrations**: Sempre crie migrações para mudanças em models
4. **Backup**: Faça backup do banco antes de mudanças críticas

---

## 👥 Créditos

### Desenvolvimento

**SHIAI SISTEM** foi desenvolvido para modernizar e automatizar a gestão de competições de Judô, substituindo sistemas baseados em planilhas e processos manuais.

### Tecnologias Utilizadas

- **Django**: Framework web Python
- **Django REST Framework**: API REST
- **SQLite**: Banco de dados (desenvolvimento)
- **Inter Font**: Tipografia (Google Fonts)
- **Heroicons/Feather Icons**: Ícones SVG

### Licença

Este é um sistema proprietário desenvolvido para uso específico em competições de Judô.

---

## 📞 Suporte

Para dúvidas, problemas ou sugestões:

1. Consulte a documentação em `/docs/` (se disponível)
2. Verifique os arquivos de especificação:
   - `ESPECIFICACAO_ESTILIZACAO_ADMIN.md`
   - `ESPECIFICACAO_FORMULARIOS_ADMIN.md`
   - `ELEGIBILIDADE_CATEGORIAS.md`
   - `TIPOS_DE_CHAVES.md`
3. Abra uma issue no repositório (se aplicável)

---

## 🔄 Changelog

### Versão Atual

- ✅ Sistema completo de gestão de competições
- ✅ Módulo de administração com dashboard executivo
- ✅ Módulo de academias com login independente
- ✅ Geração automática de chaves
- ✅ Sistema financeiro completo
- ✅ Relatórios e métricas
- ✅ Design System SHIAI unificado
- ✅ Mobile-first e responsivo

---

**Desenvolvido com ❤️ para o Judô Brasileiro**
=======
# Sistema de Gestão de Competições de Judô

Sistema Django completo para gestão de competições de Judô, replicando a lógica de planilhas Excel com macros VBA.

## Funcionalidades

1. **Cadastro de Atletas** - Inscrição com cálculo automático de classe e categoria
2. **Tabela Oficial de Categorias** - Gestão de categorias por classe, sexo e peso
3. **Inscrição Automática** - Sistema calcula idade, classe e categorias permitidas
4. **Pesagem** - Registro de peso oficial com ajuste automático de categoria
5. **Eliminação Automática** - Elimina atletas por excesso de peso
6. **Geração Automática de Chaves** - Chaves olímpicas, triangular, melhor de 3, etc.
7. **Registro de Resultados** - Registro de vencedores de cada luta
8. **Pódio Automático** - Definição automática de 1º, 2º, 3º e 3º
9. **Pontuação por Academia** - Cálculo automático de pontos
10. **Ranking Final** - Ranking das academias
11. **Relatórios HTML** - Relatórios simples em HTML

## Instalação e Uso

### Requisitos
- Python 3.8+
- Django 5.2+

### Instalação

1. Clone ou baixe o projeto
2. Instale o Django:
```bash
pip install django
```

3. Execute as migrations:
```bash
python manage.py migrate
```

4. Crie um superusuário (opcional, para acessar o admin):
```bash
python manage.py createsuperuser
```

5. Execute o servidor:
```bash
python manage.py runserver
```

6. Acesse o sistema em: http://127.0.0.1:8000/

### Fluxo de Uso

1. **Cadastrar Academias** - Vá em "Academias" e cadastre as academias participantes
2. **Cadastrar Categorias** - Vá em "Categorias" e cadastre todas as categorias oficiais
3. **Cadastrar Atletas** - Vá em "Cadastrar Atleta" e inscreva os atletas
4. **Pesagem** - Vá em "Pesagem", filtre e registre o peso oficial de cada atleta
5. **Gerar Chaves** - Vá em "Chaves" > "Gerar Nova Chave" para cada categoria
6. **Registrar Lutas** - Em cada chave, registre o vencedor de cada luta
7. **Calcular Pontuação** - Após finalizar todas as chaves, calcule a pontuação
8. **Ver Ranking** - Acesse "Ranking" para ver o ranking final das academias
9. **Gerar Relatórios** - Acesse "Relatórios" para ver os relatórios

## Estrutura do Projeto

- `atletas/models.py` - Modelos (Academia, Categoria, Atleta, Chave, Luta)
- `atletas/views.py` - Views (funções)
- `atletas/utils.py` - Lógica de negócio (cálculos, geração de chaves)
- `atletas/templates/` - Templates HTML
- `atletas/admin.py` - Configuração do admin Django

## Pontuação

- **1º lugar**: 10 pontos
- **2º lugar**: 7 pontos
- **3º lugar**: 5 pontos (cada)

## Tipos de Chave

- **1 atleta**: Campeão automático
- **2 atletas**: Melhor de 3
- **3 atletas**: Triangular
- **4+ atletas**: Chave olímpica (4, 8, 16, 32)

## Observações

- O sistema não requer autenticação no MVP
- Todos os dados são salvos em SQLite (banco de dados padrão do Django)
- Os relatórios são gerados em HTML simples
- O sistema está pronto para uso em competições reais

>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
