# Guia de Criação de Dados Fictícios

Este guia explica como criar dados fictícios para testar o sistema Shiai.

## Comando Principal

```bash
python manage.py criar_dados_ficticios
```

## Opções Disponíveis

### Limpar dados existentes antes de criar novos

```bash
python manage.py criar_dados_ficticios --clear
```

### Personalizar quantidade de dados

```bash
# Criar 3 organizadores, 8 academias por organizador, 100 atletas
python manage.py criar_dados_ficticios --organizadores 3 --academias 8 --atletas 100
```

### Combinar opções

```bash
# Limpar tudo e criar dados personalizados
python manage.py criar_dados_ficticios --clear --organizadores 2 --academias 5 --atletas 50
```

## O que o comando cria

1. **Classes e Categorias**: Verifica se existem, cria classes básicas se necessário
2. **Organizadores**: Cria organizadores (padrão: 2)
3. **Academias**: Cria academias vinculadas aos organizadores (padrão: 5 por organizador)
4. **Atletas**: Cria atletas distribuídos entre academias (padrão: 50)
5. **Campeonatos**: Cria campeonatos ativos e encerrados para cada organizador
6. **Inscrições**: Cria inscrições nos campeonatos
7. **Equipe Técnica**: Cria pessoas da equipe técnica
8. **Usuários Operacionais**: Cria usuários operacionais vinculados aos organizadores
9. **Senhas de Academia**: Cria senhas de acesso para academias nos campeonatos
10. **Conferência de Pesagem**: Cria dados de pesagem para alguns atletas

## Pré-requisitos

### 1. Popular Categorias Oficiais (Recomendado)

Antes de criar dados fictícios, é recomendado popular as categorias oficiais:

```bash
python manage.py popular_categorias_oficiais
```

Este comando popula o banco com todas as categorias oficiais de judô baseadas no arquivo `categorias_oficiais_judo.json`.

### 2. Criar Superuser (Opcional)

Se quiser criar um superuser para testes:

```bash
python manage.py criar_superuser
```

## Dados Criados

### Organizadores

- Nomes realistas de federações e ligas
- Email e telefone configurados
- Status ativo por padrão

### Academias

- Distribuídas entre os organizadores
- Nomes de academias reais da região
- Cidades e estados variados
- Telefones e endereços fictícios

### Atletas

- Nomes brasileiros realistas
- Distribuídos em diferentes classes (FESTIVAL até VETERANOS)
- Faixas variadas
- Alguns federados, outros não
- Números Zempo para federados

### Campeonatos

- Campeonatos ativos com datas futuras
- Campeonatos encerrados com datas passadas
- Valores de inscrição configurados
- Chaves PIX configuradas

### Usuários Operacionais

- Username: `test_operacional_<id_organizador>`
- Senha padrão: `test1234`
- Vinculados aos organizadores via UserProfile
- Primeiro usuário tem permissões de resetar e criar usuários

### Senhas de Academia

- Login: `ACADEMIA_<id>` (ex: ACADEMIA_001)
- Senha: Gerada aleatoriamente (8 caracteres)
- Expiração: 5 dias após término do campeonato

## Exemplo de Uso Completo

```bash
# 1. Popular categorias oficiais (se ainda não fez)
python manage.py popular_categorias_oficiais

# 2. Criar dados fictícios básicos
python manage.py criar_dados_ficticios

# 3. Ou limpar e criar dados personalizados
python manage.py criar_dados_ficticios --clear --organizadores 3 --academias 6 --atletas 80
```

## Limpeza de Dados

⚠️ **ATENÇÃO**: O comando `--clear` remove TODOS os dados de teste, mas preserva:
- Superusers
- Usuários que não começam com `test_`
- Classes e Categorias (apenas verifica se existem)

Para limpar completamente (incluindo categorias), você precisaria fazer manualmente ou usar migrações.

## Resolução de Problemas

### Erro: "Nenhuma categoria encontrada"

Execute primeiro:
```bash
python manage.py popular_categorias_oficiais
```

### Erro: "Organizador não encontrado"

O comando cria organizadores automaticamente. Se houver erro, verifique se o modelo `Organizador` está correto.

### Dados não aparecem na interface

1. Verifique se está logado com um usuário operacional
2. Verifique se o usuário está vinculado ao organizador correto
3. Verifique se o campeonato está ativo

## Dicas

1. **Primeira execução**: Use `--clear` para garantir um estado limpo
2. **Testes rápidos**: Use valores menores (--organizadores 1 --academias 3 --atletas 20)
3. **Testes completos**: Use valores maiores (--organizadores 3 --academias 10 --atletas 100)
4. **Desenvolvimento**: Execute sem `--clear` para adicionar dados incrementais

## Credenciais de Teste

Após executar o comando, você terá:

- **Usuários Operacionais**: 
  - Username: `test_operacional_<id>`
  - Senha: `test1234`
  - Vinculados aos organizadores criados

- **Senhas de Academia**:
  - Login: `ACADEMIA_<id>` (ex: ACADEMIA_001)
  - Senha: Gerada aleatoriamente (verifique no banco ou gere novamente)

## Próximos Passos

Após criar os dados fictícios:

1. Faça login com um usuário operacional
2. Navegue pelo dashboard
3. Teste as funcionalidades:
   - Cadastro de atletas
   - Inscrições em campeonatos
   - Pesagem
   - Geração de chaves
   - Relatórios

