# 📋 Detalhamento Completo do Projeto - Sistema de Gestão de Competições de Judô

## 🎯 Visão Geral

Sistema Django completo para gestão de competições de Judô, desenvolvido para substituir planilhas Excel com macros VBA. O sistema automatiza todo o processo desde a inscrição de atletas até a geração de rankings e relatórios finais.

---

## 🏗️ Arquitetura e Tecnologias

### Stack Tecnológico
- **Backend**: Django 5.2.8
- **API**: Django REST Framework
- **Banco de Dados**: SQLite (desenvolvimento)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Design**: Responsivo com suporte mobile/desktop

### Estrutura do Projeto
```
Shiai_sistem/
├── judocomp/              # Configurações do projeto Django
│   ├── settings.py         # Configurações principais
│   ├── urls.py            # URLs principais
│   └── wsgi.py            # WSGI config
├── atletas/               # App principal
│   ├── models.py          # Modelos de dados
│   ├── views.py           # Views (32 funções)
│   ├── urls.py            # Rotas da aplicação
│   ├── utils.py           # Lógica de negócio (729 linhas)
│   ├── middleware.py      # Detecção mobile/desktop
│   ├── admin.py           # Admin Django
│   ├── templates/         # Templates HTML (25 arquivos)
│   └── management/       # Comandos customizados (10 comandos)
└── requirements.txt       # Dependências
```

---

## 📊 Modelos de Dados (7 Modelos)

### 1. **Academia**
- `nome` - Nome da academia
- `cidade` - Cidade
- `estado` - Estado (2 caracteres)
- `pontos` - Pontuação total (calculada)

### 2. **Categoria**
- `classe` - SUB 9, SUB 11, SUB 13, SUB 15, SUB 18, SUB 21, SÊNIOR
- `sexo` - Masculino (M) ou Feminino (F)
- `categoria_nome` - Nome da categoria (ex: "Meio Leve")
- `limite_min` - Peso mínimo (kg)
- `limite_max` - Peso máximo (kg) ou 999.0 para "acima de"
- `label` - Rótulo completo (ex: "SUB 11 - Meio Leve")

### 3. **Atleta**
- **Dados Básicos**:
  - `nome`, `ano_nasc`, `sexo`, `faixa`
  - `academia` (ForeignKey)
  
- **Campos Calculados na Inscrição**:
  - `classe` - Calculada automaticamente pela idade
  - `categoria_nome` - Categoria inicial
  - `categoria_limite` - Limites da categoria
  - `peso_previsto` - Peso informado na inscrição
  
- **Campos da Pesagem**:
  - `peso_oficial` - Peso registrado na pesagem
  - `categoria_ajustada` - Nova categoria se houver remanejamento
  - `motivo_ajuste` - Motivo do ajuste
  - `status` - OK, Eliminado Peso, Eliminado Indisciplina
  - `remanejado` - Boolean indicando remanejamento

- **Propriedades**:
  - `idade` - Calculada automaticamente
  - `get_categoria_atual()` - Retorna categoria atual
  - `get_limite_categoria()` - Retorna limites formatados

### 4. **Chave**
- `classe` - Classe da chave
- `sexo` - Masculino ou Feminino
- `categoria` - Nome da categoria
- `atletas` - ManyToMany com atletas participantes
- `estrutura` - JSON com estrutura da chave (árvore de lutas)

### 5. **Luta**
- `chave` - ForeignKey para Chave
- `atleta_a` - Primeiro atleta (pode ser null para BYE)
- `atleta_b` - Segundo atleta (pode ser null para BYE)
- `vencedor` - Atleta vencedor
- `round` - Número do round (1, 2, 3...)
- `proxima_luta` - ID da próxima luta na chave
- `concluida` - Boolean
- `tipo_vitoria` - IPPON, WAZARI, WAZARI_WAZARI, YUKO
- `pontos_vencedor` - Pontos do vencedor
- `pontos_perdedor` - Pontos do perdedor
- `ippon_count`, `wazari_count`, `yuko_count` - Contadores

### 6. **AdminLog**
- `data_hora` - Data e hora da ação
- `acao` - Descrição da ação
- `usuario_ip` - IP do usuário

### 7. **Campeonato**
- `nome` - Nome do campeonato
- `data_inicio` - Data de início
- `data_fim` - Data de término
- `ativo` - Boolean

### 8. **AcademiaPontuacao**
- `campeonato` - ForeignKey para Campeonato
- `academia` - ForeignKey para Academia
- `ouro`, `prata`, `bronze`, `quarto`, `quinto` - Contadores de medalhas
- `festival` - Pontos do festival
- `remanejamento` - Penalidade por remanejamento
- `pontos_totais` - Total calculado

---

## 🎨 Interface e Design

### Tema Visual
- **Cores Principais**: 
  - Vermelho: `#dc3545`
  - Cinza Grafite: `#2f2f2f`
  - Gradiente: `linear-gradient(135deg, #dc3545 0%, #2f2f2f 100%)`

### Sidebar de Navegação
- **Desktop**: Sidebar fixa no lado esquerdo (250px)
- **Mobile**: Menu hambúrguer com overlay
- **Itens do Menu**:
  1. 🏠 Início
  2. 🏫 Academias
  3. 👥 Atletas
  4. ➕ Cadastrar Atleta
  5. 🏅 Festival
  6. 📋 Categorias
  7. ⚖️ Pesagem
  8. 🥋 Chaves
  9. 🏆 Ranking
  10. 📊 Dashboard
  11. 📄 Relatórios
  12. 🔄 Resetar Campeonato

### Templates Responsivos
- **Desktop**: Layout completo com sidebar
- **Mobile**: Versões otimizadas para:
  - Pesagem (`pesagem_mobile.html`)
  - Chaves (`chave_mobile.html`)
  - Lutas (`luta_mobile.html`)

---

## 🔧 Funcionalidades Implementadas

### 1. **Gestão de Academias**
- ✅ Listar academias
- ✅ Cadastrar nova academia
- ✅ Visualizar pontuação por academia

### 2. **Gestão de Categorias**
- ✅ Listar categorias com filtros (classe, sexo, nome)
- ✅ Cadastrar nova categoria
- ✅ Sistema de limites de peso (incluindo "acima de")

### 3. **Gestão de Atletas**
- ✅ Listar atletas com filtros avançados
- ✅ Cadastrar atleta individual
  - Cálculo automático de classe pela idade
  - Seleção de categoria baseada em classe e sexo
  - Validação de dados
- ✅ Cadastrar Festival (atletas de 3-6 anos)
- ✅ Importar atletas via CSV
  - Validação de dados
  - Tratamento de erros
  - Feedback detalhado
- ✅ AJAX para buscar categorias dinamicamente

### 4. **Sistema de Pesagem**
- ✅ Interface desktop e mobile
- ✅ Filtros por classe, sexo e categoria
- ✅ Registro de peso oficial
- ✅ **Ajuste Automático de Categoria**:
  - Verifica se peso está dentro dos limites
  - Se acima: busca categoria superior ou elimina
  - Se abaixo: busca categoria correta
  - Modal de confirmação para remanejamento
- ✅ **Remanejamento**:
  - Penalidade de -1 ponto para academia
  - Opção de desclassificar ao invés de remanejar
  - Registro do motivo do ajuste
- ✅ Status visual (OK, Eliminado, Remanejado)

### 5. **Geração de Chaves**
- ✅ **Geração Automática**:
  - 1 atleta: Campeão automático
  - 2 atletas: Melhor de 3
  - 3 atletas: Triangular
  - 4+ atletas: Chave olímpica (4, 8, 16, 32)
- ✅ **Geração Manual** (Lutas Casadas):
  - Seleção manual de atletas
  - Criação de lutas específicas
- ✅ Visualização de chaves (desktop e mobile)
- ✅ Estrutura em árvore (JSON)

### 6. **Registro de Lutas**
- ✅ Interface desktop e mobile
- ✅ Seleção de vencedor
- ✅ Tipo de vitória:
  - Ippon (10 pontos)
  - Wazari (7 pontos)
  - Wazari-Wazari (7 pontos)
  - Yuko (1 ponto)
- ✅ Cálculo automático de pontos
- ✅ Atualização automática da próxima luta
- ✅ Tratamento de BYE (Walk Over)

### 7. **Sistema de Pontuação**
- ✅ **Pontuação por Posição**:
  - 1º lugar: 10 pontos
  - 2º lugar: 7 pontos
  - 3º lugar: 5 pontos (cada)
- ✅ **Penalidades**:
  - Remanejamento: -1 ponto
- ✅ Cálculo automático de pontuação por academia
- ✅ Contagem de medalhas (ouro, prata, bronze)

### 8. **Ranking**
- ✅ Ranking de academias ordenado por pontos
- ✅ API REST para ranking (`/api/ranking/academias/`)
- ✅ Visualização com estatísticas

### 9. **Relatórios**
- ✅ **Dashboard**:
  - Total de atletas
  - Atletas OK
  - Atletas Festival
  - Gráficos por classe
  - Gráficos por academia
  - Medalhas por academia
- ✅ **Relatório de Atletas Inscritos**
- ✅ **Relatório de Pesagem Final**
- ✅ **Relatório de Chaves**
- ✅ **Relatório de Resultados por Categoria**

### 10. **Funcionalidades Administrativas**
- ✅ Reset completo do campeonato (com senha)
  - Zera todas as lutas
  - Zera pontuações
  - Reseta pesagens e remanejamentos
  - Mantém atletas, academias e categorias
- ✅ Logs administrativos
- ✅ Middleware de detecção mobile/desktop

---

## 🛠️ Lógica de Negócio (utils.py - 729 linhas)

### Funções Principais

1. **`calcular_classe(ano_nasc)`**
   - Calcula classe baseada na idade:
     - ≤ 6 anos: Festival
     - ≤ 8 anos: SUB 9
     - ≤ 10 anos: SUB 11
     - ≤ 12 anos: SUB 13
     - ≤ 14 anos: SUB 15
     - ≤ 17 anos: SUB 18
     - ≤ 20 anos: SUB 21
     - > 20 anos: SÊNIOR

2. **`get_categorias_disponiveis(classe, sexo)`**
   - Retorna categorias disponíveis ordenadas por peso

3. **`ajustar_categoria_por_peso(atleta, peso_oficial)`**
   - Lógica complexa de ajuste:
     - Verifica se peso está dentro dos limites
     - Se acima: busca categoria superior ou elimina
     - Se abaixo: busca categoria correta
     - Retorna nova categoria e motivo

4. **`gerar_chave(atletas, classe, sexo, categoria)`**
   - Gera estrutura de chave baseada no número de atletas
   - Cria lutas e conecta rounds
   - Tratamento de BYE

5. **`get_resultados_chave(chave)`**
   - Extrai resultados finais da chave
   - Ordena por posição (1º, 2º, 3º, 3º)

6. **`calcular_pontuacao_academias()`**
   - Calcula pontuação total por academia
   - Conta medalhas
   - Aplica penalidades

7. **`atualizar_proxima_luta(luta, vencedor)`**
   - Atualiza próxima luta na chave
   - Conecta rounds automaticamente

8. **`registrar_remanejamento(atleta, categoria_antiga, categoria_nova)`**
   - Registra remanejamento
   - Aplica penalidade

---

## 📱 Middleware Mobile

### Funcionalidades
- ✅ Detecção automática de dispositivos móveis
- ✅ Redirecionamento automático para versões mobile:
  - `/pesagem` → `/pesagem/mobile/`
  - `/chaves/{id}/` → `/chave/mobile/{id}/`
- ✅ Detecção por User-Agent e largura de tela
- ✅ Cookie para armazenar largura da tela
- ✅ Parâmetro `?desktop=1` para forçar versão desktop

---

## 🎯 Comandos de Gerenciamento (10 comandos)

1. **`popular_categorias`** - Popula categorias oficiais
2. **`recalcular_classes_atletas`** - Recalcula classes de todos os atletas
3. **`gerar_todas_chaves`** - Gera chaves para todas as categorias
4. **`aprovar_todos_pesagem`** - Aprova todos os atletas na pesagem
5. **`corrigir_categorias_extra_ligeiro`** - Corrige categorias específicas
6. **`corrigir_classes_verbo_divino`** - Corrige classes específicas
7. **`corrigir_limites_categorias`** - Corrige limites de categorias
8. **`importar_festival_verbo_divino`** - Importa dados específicos
9. **`importar_verbo_divino_inclusao`** - Importa inclusões específicas

---

## 🔐 Segurança e Configurações

### Settings Atuais
- ✅ Django 5.2.8
- ✅ SQLite (desenvolvimento)
- ✅ DEBUG = True (desenvolvimento)
- ✅ ALLOWED_HOSTS = ['*'] (ajustar em produção)
- ✅ SECRET_KEY (ajustar em produção)
- ✅ Django REST Framework configurado
- ✅ Middleware de segurança ativo
- ✅ CSRF Protection ativo

### Melhorias Necessárias para Produção
- ⚠️ Mover SECRET_KEY para variável de ambiente
- ⚠️ Definir ALLOWED_HOSTS específicos
- ⚠️ DEBUG = False
- ⚠️ Configurar banco de dados PostgreSQL/MySQL
- ⚠️ Configurar arquivos estáticos (STATIC_ROOT, STATICFILES_DIRS)
- ⚠️ Configurar HTTPS
- ⚠️ Adicionar autenticação de usuários

---

## 📈 Estatísticas do Projeto

### Código
- **Views**: 32 funções + 1 classe API
- **Models**: 8 modelos
- **Templates**: 25 arquivos HTML
- **URLs**: 55 rotas
- **Utils**: 729 linhas de lógica de negócio
- **Comandos**: 10 comandos customizados

### Funcionalidades
- ✅ 100% das funcionalidades básicas implementadas
- ✅ Interface responsiva (mobile + desktop)
- ✅ Sistema de relatórios completo
- ✅ API REST para ranking
- ✅ Importação de dados via CSV
- ✅ Sistema de logs administrativos

---

## 🚀 Fluxo de Uso Completo

1. **Configuração Inicial**:
   - Cadastrar academias participantes
   - Cadastrar categorias oficiais (ou usar comando `popular_categorias`)

2. **Inscrição**:
   - Cadastrar atletas individualmente ou
   - Importar atletas via CSV
   - Sistema calcula automaticamente classe e categoria

3. **Pesagem**:
   - Registrar peso oficial de cada atleta
   - Sistema ajusta categoria se necessário
   - Aplicar remanejamento ou desclassificação

4. **Geração de Chaves**:
   - Gerar chaves automaticamente ou manualmente
   - Sistema cria estrutura de lutas

5. **Registro de Lutas**:
   - Registrar vencedor de cada luta
   - Sistema atualiza automaticamente a chave

6. **Cálculo de Pontuação**:
   - Calcular pontuação de todas as academias
   - Visualizar ranking

7. **Relatórios**:
   - Gerar relatórios finais
   - Dashboard com estatísticas

---

## 🎨 Melhorias Recentes (Branch: ajustes-projeto)

### ✅ Implementado
1. **Tema Visual**: Cores ajustadas para vermelho e cinza grafite
2. **Sidebar**: Navegação lateral implementada
3. **Responsividade**: Melhorias em mobile
4. **Estrutura**: Correções em settings.py e requirements.txt

---

## 📝 Observações Importantes

- O sistema não requer autenticação no MVP atual
- Todos os dados são salvos em SQLite (padrão Django)
- Relatórios são gerados em HTML simples
- Sistema está pronto para uso em competições reais
- Middleware mobile funciona automaticamente
- Reset de campeonato requer senha de administrador

---

## 🔄 Próximos Passos Sugeridos

1. **Segurança**:
   - Implementar autenticação de usuários
   - Configurar permissões por módulo
   - Mover configurações sensíveis para variáveis de ambiente

2. **Performance**:
   - Otimizar queries do banco de dados
   - Implementar cache para relatórios
   - Considerar PostgreSQL para produção

3. **Funcionalidades**:
   - Exportação de relatórios em PDF
   - Notificações em tempo real
   - Histórico de competições
   - Backup automático

4. **Interface**:
   - Melhorar UX em mobile
   - Adicionar gráficos interativos
   - Dark mode

---

**Última atualização**: Branch `ajustes-projeto` - Ajustes de tema e sidebar implementados

