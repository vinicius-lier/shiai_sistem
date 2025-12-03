# 📋 Guia: Como Criar uma Nova Organização

Este guia explica como criar uma nova organização quando um novo cliente compra o sistema.

## 🎯 Fluxo Completo

### Passo 1: Criar o Organizador

Execute o comando para criar a organização:

```bash
python manage.py criar_organizador \
  --nome "Nome da Organização" \
  --email contato@organizacao.com \
  --telefone "(00) 00000-0000"
```

**Exemplo:**
```bash
python manage.py criar_organizador \
  --nome "Federação Paulista de Judô" \
  --email contato@fpj.com.br \
  --telefone "(11) 98765-4321"
```

### Passo 2: Criar Usuário Organizador

Crie o usuário principal da organização (que terá acesso operacional):

```bash
python manage.py criar_usuario_principal \
  --username organizador_fpj \
  --password SenhaSegura123! \
  --email admin@fpj.com.br \
  --first-name "João" \
  --last-name "Silva"
```

### Passo 3: Associar Usuário ao Organizador

Associe o usuário criado à organização:

```bash
python manage.py criar_organizador \
  --nome "Federação Paulista de Judô" \
  --email contato@fpj.com.br \
  --usuario organizador_fpj
```

**OU** use o Django Admin:
1. Acesse `/admin/`
2. Vá em **Atletas > Perfis de Usuário**
3. Encontre o usuário e edite
4. Selecione o organizador no campo "Organizador"
5. Salve

### Passo 4: Verificar

Verifique se tudo está correto:

```bash
python manage.py shell
```

```python
from atletas.models import Organizador, UserProfile
from django.contrib.auth.models import User

# Ver organizador
org = Organizador.objects.get(nome="Federação Paulista de Judô")
print(f"Organizador: {org.nome}")
print(f"Email: {org.email}")

# Ver usuário associado
user = User.objects.get(username="organizador_fpj")
profile = user.profile
print(f"Usuário: {user.username}")
print(f"Organizador: {profile.organizador.nome if profile.organizador else 'Nenhum'}")
```

## 🔄 Fluxo Automatizado (Recomendado)

Para facilitar, você pode criar um script que faz tudo de uma vez:

```bash
#!/bin/bash
# criar_nova_organizacao.sh

ORGANIZACAO_NOME="$1"
ORGANIZACAO_EMAIL="$2"
ORGANIZACAO_TELEFONE="$3"
USUARIO_USERNAME="$4"
USUARIO_PASSWORD="$5"
USUARIO_EMAIL="$6"

# Criar organizador
python manage.py criar_organizador \
  --nome "$ORGANIZACAO_NOME" \
  --email "$ORGANIZACAO_EMAIL" \
  --telefone "$ORGANIZACAO_TELEFONE"

# Criar usuário
python manage.py criar_usuario_principal \
  --username "$USUARIO_USERNAME" \
  --password "$USUARIO_PASSWORD" \
  --email "$USUARIO_EMAIL"

# Associar usuário ao organizador
python manage.py criar_organizador \
  --nome "$ORGANIZACAO_NOME" \
  --email "$ORGANIZACAO_EMAIL" \
  --usuario "$USUARIO_USERNAME"

echo "✅ Organização criada com sucesso!"
```

**Uso:**
```bash
chmod +x criar_nova_organizacao.sh
./criar_nova_organizacao.sh \
  "Federação Paulista de Judô" \
  "contato@fpj.com.br" \
  "(11) 98765-4321" \
  "organizador_fpj" \
  "SenhaSegura123!" \
  "admin@fpj.com.br"
```

## 📝 Via Django Admin (Interface Gráfica)

### 1. Criar Organizador

1. Acesse `/admin/`
2. Vá em **Atletas > Organizadores**
3. Clique em **Adicionar Organizador**
4. Preencha:
   - **Nome do Organizador**: Nome da organização
   - **E-mail**: Email de contato
   - **Telefone**: Telefone (opcional)
   - **Logo**: Upload do logo (opcional)
5. Clique em **Salvar**

### 2. Criar Usuário

1. Vá em **Autenticação e Autorização > Usuários**
2. Clique em **Adicionar Usuário**
3. Preencha:
   - **Nome de usuário**: Login único
   - **Senha**: Senha segura
   - **E-mail**: Email do usuário
4. Clique em **Salvar**
5. Complete o perfil:
   - **Primeiro nome**: Nome
   - **Último nome**: Sobrenome
   - Marque **Ativo** e **Equipe de funcionários** (se necessário)
6. Clique em **Salvar**

### 3. Associar Usuário ao Organizador

1. Vá em **Atletas > Perfis de Usuário**
2. Clique em **Adicionar Perfil de Usuário**
3. Selecione:
   - **Usuário**: O usuário criado
   - **Organizador**: A organização criada
4. Clique em **Salvar**

### 4. Configurar Permissões Operacionais

1. Vá em **Atletas > Usuários Operacionais**
2. Clique em **Adicionar Usuário Operacional**
3. Selecione:
   - **Usuário**: O usuário criado
   - **Pode Resetar Campeonato**: ✅ (se for o principal)
   - **Pode Criar Usuários**: ✅ (se for o principal)
   - **Data de Expiração**: Deixe em branco para vitalício
   - **Ativo**: ✅
4. Clique em **Salvar**

## ✅ Checklist de Criação

- [ ] Organizador criado
- [ ] Usuário criado
- [ ] Usuário associado ao organizador
- [ ] Perfil operacional criado
- [ ] Permissões configuradas
- [ ] Login testado
- [ ] Dados isolados verificados

## 🔒 Segurança

- ✅ Cada organização vê apenas seus próprios dados
- ✅ Usuários só acessam dados do seu organizador
- ✅ Isolamento total entre organizações
- ✅ Sem risco de vazamento de dados entre clientes

## 📊 Próximos Passos Após Criar

1. **Criar Campeonato**: O organizador pode criar seus campeonatos
2. **Cadastrar Academias**: Academias serão automaticamente associadas ao organizador
3. **Cadastrar Atletas**: Atletas pertencem às academias (isolamento automático)
4. **Criar Eventos**: Eventos isolados por organizador

## 🆘 Troubleshooting

**Problema:** Usuário não vê dados
- **Solução:** Verificar se `user.profile.organizador` está configurado

**Problema:** Organizador não aparece no admin
- **Solução:** Verificar se o usuário tem permissões de staff

**Problema:** Dados de outra organização aparecem
- **Solução:** Verificar se as views estão filtrando por `request.user.profile.organizador`

