# Auditoria de Banco de Dados — SHIAI

## Visão Geral
- Tipo de banco: PostgreSQL
- ORM utilizado: Django ORM
- Ambiente: multi‑organização (Organizador) com múltiplas academias e múltiplos eventos
- Observações de arquitetura: dados operacionais são multi‑tenant por Organizador; academia não cria eventos; inscrições conectam atletas, eventos e categorias; rankings dependem de eventos encerrados.

## Diagrama Conceitual (texto)
- Organizador 1:N Academia
- Organizador 1:N Campeonato
- Academia 1:N Atleta
- Campeonato 1:N Inscricao
- Classe 1:N Categoria
- Classe 1:N Inscricao (classe_real)
- Categoria 1:N Inscricao (categoria_real)
- Campeonato N:N Academia (via AcademiaCampeonato)
- Campeonato N:N Academia (via AcademiaCampeonatoSenha)
- Campeonato 1:N Chave
- Chave N:N Atleta
- Inscricao 1:N PesagemHistorico
- Campeonato 1:N PesagemHistorico
- Campeonato 1:N AcademiaPontuacao
- Academia 1:N AcademiaPontuacao
- Campeonato 1:N EquipeTecnicaCampeonato
- EquipeTecnicaCampeonato 1:N PessoaEquipeTecnica
- CategoriaInsumo 1:N InsumoEstrutura
- Campeonato N:N FormaPagamento

## Entidades Principais

### Organizador
Campos:
- id (PK)
- nome (string)
- email (string, opcional)
- telefone (string, opcional)
- owner_id (FK User, opcional)
- logo (arquivo, opcional)
- slug (string, único, opcional)
- data_criacao (datetime)
- ativo (boolean)

Chaves:
- PK: id
- FKs: owner_id -> User

Relações:
- 1:N com Academia
- 1:N com Campeonato

Regras de Negócio:
- Organizador cria e gerencia eventos.
- Um organizador contém múltiplas academias.

Observações Técnicas:
- slug deve ser único (gerado automaticamente).
- ativo controla visibilidade e acesso.

### Academia
Campos:
- id (PK)
- organizador_id (FK Organizador)
- nome (string)
- cidade (string)
- estado (string)
- telefone (string, opcional)
- responsavel (string, opcional)
- endereco (string, opcional)
- pontos (int)
- foto_perfil (arquivo, opcional)
- ativo_login (boolean)

Chaves:
- PK: id
- FK: organizador_id -> Organizador

Relações:
- 1:N com Atleta
- N:N com Campeonato (via AcademiaCampeonato)
- N:N com Campeonato (via AcademiaCampeonatoSenha)
- 1:N com AcademiaPontuacao

Regras de Negócio:
- Academia não cria eventos.
- Academia inscreve atletas em campeonatos permitidos.

Observações Técnicas:
- organizador_id obrigatório para consistência multi‑tenant.

### Campeonato (Evento)
Campos:
- id (PK)
- organizador_id (FK Organizador)
- nome (string)
- data_inicio (date, opcional)
- data_competicao (date, opcional)
- data_limite_inscricao (date, opcional)
- data_limite_inscricao_academia (date, opcional)
- ativo (boolean)
- regulamento (text, opcional)
- valor_inscricao_federado (decimal, opcional)
- valor_inscricao_nao_federado (decimal, opcional)
- chave_pix (string, opcional)
- titular_pix (string, opcional)

Chaves:
- PK: id
- FK: organizador_id -> Organizador

Relações:
- 1:N com Inscricao
- 1:N com Chave
- 1:N com PesagemHistorico
- 1:N com AcademiaPontuacao
- N:N com FormaPagamento

Regras de Negócio:
- Apenas um campeonato ativo por organizador.
- Eventos encerrados não permitem novas inscrições.

Observações Técnicas:
- data_competicao controla encerramento.
- valores de inscrição usados no cálculo financeiro.

### Atleta
Campos:
- id (PK)
- nome (string)
- data_nascimento (date, opcional)
- ano_nasc (int, legado)
- sexo (char)
- academia_id (FK Academia)
- classe_inicial (string, opcional)
- documento_oficial (arquivo, opcional)
- foto_perfil (arquivo, opcional)
- status_ativo (boolean)

Chaves:
- PK: id
- FK: academia_id -> Academia

Relações:
- 1:N com Inscricao

Regras de Negócio:
- Atleta pertence a uma academia.
- Classe etária é calculada pelo ano do evento (não por mês/dia).

Observações Técnicas:
- data_nascimento é preferível; ano_nasc mantém compatibilidade.

### Classe (Etária)
Campos:
- id (PK)
- nome (string)
- idade_min (int)
- idade_max (int)

Chaves:
- PK: id

Relações:
- 1:N com Categoria
- 1:N com Inscricao (classe_real)

Regras de Negócio:
- Classe é determinada pela idade no ano do evento.

Observações Técnicas:
- Nome usado para normalização em regras de elegibilidade.

### Categoria (Peso)
Campos:
- id (PK)
- classe_id (FK Classe)
- sexo (char)
- categoria_nome (string)
- limite_min (decimal)
- limite_max (decimal, opcional)
- label (string)

Chaves:
- PK: id
- FK: classe_id -> Classe

Relações:
- 1:N com Inscricao (categoria_real)

Regras de Negócio:
- Categoria depende de classe e sexo.
- limite_max pode ser nulo/999 para “acima de”.

Observações Técnicas:
- label deve ser único por classe/sexo para exibição.

### Inscricao
Campos:
- id (PK)
- atleta_id (FK Atleta)
- campeonato_id (FK Campeonato)
- classe_escolhida (string, legado)
- categoria_calculada (string, opcional)
- categoria_escolhida (string, opcional)
- classe_real_id (FK Classe, opcional)
- categoria_real_id (FK Categoria, opcional)
- peso_real (decimal, opcional)
- status_atual (enum)
- peso_informado (decimal, opcional)
- peso (decimal, opcional)
- categoria_ajustada (string, opcional)
- motivo_ajuste (text, opcional)
- remanejado (boolean)
- bloqueado_chave (boolean)
- status_inscricao (enum legado)
- data_inscricao (datetime)
- data_pesagem (datetime, opcional)

Chaves:
- PK: id
- FK: atleta_id -> Atleta
- FK: campeonato_id -> Campeonato
- FK: classe_real_id -> Classe
- FK: categoria_real_id -> Categoria

Relações:
- N:1 com Atleta
- N:1 com Campeonato

Regras de Negócio:
- Inscrição liga atleta + evento + classe/categoria.
- Permite múltiplas inscrições do mesmo atleta no mesmo evento, desde que classe/categoria diferentes.

Observações Técnicas:
- unique_together (atleta, campeonato, classe_escolhida, categoria_escolhida).
- status_atual substitui status_inscricao (legado).

### Chave
Campos:
- id (PK)
- campeonato_id (FK Campeonato, opcional)
- classe (string)
- sexo (char)
- categoria (string)
- estrutura (json)

Chaves:
- PK: id
- FK: campeonato_id -> Campeonato

Relações:
- N:N com Atleta

Regras de Negócio:
- Chave depende de evento encerrado/validado.

Observações Técnicas:
- estrutura armazenada em JSON.

### Luta
Campos:
- id (PK)
- chave_id (FK Chave)
- atleta_azul_id (FK Atleta, opcional)
- atleta_branco_id (FK Atleta, opcional)
- vencedor_id (FK Atleta, opcional)
- tipo_vitoria (enum)
- fase (string)

Chaves:
- PK: id
- FKs: chave_id -> Chave, atleta_azul_id -> Atleta, atleta_branco_id -> Atleta, vencedor_id -> Atleta

Relações:
- N:1 com Chave

Regras de Negócio:
- Resultado alimenta ranking.

Observações Técnicas:
- Integridade do vencedor deve ser garantida por regra de aplicação.

### AcademiaCampeonato (tabela pivô)
Campos:
- id (PK)
- academia_id (FK Academia)
- campeonato_id (FK Campeonato)
- permitido (boolean)

Chaves:
- PK: id
- FKs: academia_id -> Academia, campeonato_id -> Campeonato

Relações:
- N:N entre Academia e Campeonato

Regras de Negócio:
- Controla permissão da academia para participar do evento.

### AcademiaCampeonatoSenha (tabela pivô)
Campos:
- id (PK)
- academia_id (FK Academia)
- campeonato_id (FK Campeonato)
- login (string)
- senha_hash (string)
- senha_plana (string, legado)
- data_expiracao (datetime, opcional)

Chaves:
- PK: id
- FKs: academia_id -> Academia, campeonato_id -> Campeonato

Relações:
- N:N entre Academia e Campeonato

Regras de Negócio:
- Controla acesso da academia ao evento.

### AcademiaPontuacao
Campos:
- id (PK)
- academia_id (FK Academia)
- campeonato_id (FK Campeonato)
- ouro, prata, bronze (int)
- pontos_totais (int)

Chaves:
- PK: id
- FKs: academia_id -> Academia, campeonato_id -> Campeonato

Relações:
- N:1 com Academia
- N:1 com Campeonato

Regras de Negócio:
- Ranking depende de eventos encerrados.

### PesagemHistorico
Campos:
- id (PK)
- inscricao_id (FK Inscricao)
- campeonato_id (FK Campeonato)
- peso_registrado (decimal)
- categoria_ajustada (string, opcional)
- motivo_ajuste (text, opcional)
- observacoes (text, opcional)
- pesado_por_id (FK User, opcional)
- data_hora (datetime)

Chaves:
- PK: id
- FKs: inscricao_id -> Inscricao, campeonato_id -> Campeonato, pesado_por_id -> User

Relações:
- N:1 com Inscricao
- N:1 com Campeonato

Regras de Negócio:
- Histórico não deve ser apagado (auditoria de pesagem).

### FormaPagamento
Campos:
- id (PK)
- tipo (enum)
- nome (string)
- ativo (boolean)

Chaves:
- PK: id

Relações:
- N:N com Campeonato

Regras de Negócio:
- Formas de pagamento configuradas por evento.

### UsuarioOperacional
Campos:
- id (PK)
- user_id (FK User)
- organizador_id (FK Organizador)
- role (string)

Chaves:
- PK: id
- FKs: user_id -> User, organizador_id -> Organizador

Relações:
- N:1 com Organizador

Regras de Negócio:
- Organizador gerencia equipe operacional.

## Tabelas Pivô
- AcademiaCampeonato: controla permissão de participação da academia no evento.
- AcademiaCampeonatoSenha: controla credenciais de acesso por evento.
- Campeonato_FormaPagamento: habilita múltiplas formas de pagamento por evento.
- Chave_Atletas: vincula atletas às chaves.

## Fluxos Críticos
- Criação de evento: Organizador cria Campeonato, define datas, valores e formas de pagamento.
- Inscrição de atletas: Academia seleciona atleta, classe e categoria; Inscricao criada com classe_real/categoria_real.
- Encerramento de evento: data_competicao < hoje marca evento como encerrado; rankings passam a ser válidos.
- Geração de ranking: AcademiaPontuacao consolidada a partir de resultados das chaves.

## Riscos e Pontos de Atenção
- Inscricoes podem ficar órfãs se atleta/academia for removido sem proteção.
- Campos legados (classe_escolhida/categoria_escolhida/status_inscricao) podem divergir dos campos normalizados.
- Ausência de constraints para garantir “um campeonato ativo por organizador”.
- Dependência de regras no código para elegibilidade e cálculo de classe/idade.

## Sugestões de Melhoria
- Normalização: remover dependência dos campos legados após migração total.
- Constraints: unique (organizador_id, ativo) para campeonatos ativos.
- Índices: (campeonato_id, status_atual), (academia_id, campeonato_id) nas tabelas pivô.
- Status: padronizar uso de status_atual como fonte única.
- Integridade: proteger exclusão de Atleta/Academia com inscrições ativas.
