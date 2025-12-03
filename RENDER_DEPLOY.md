# 🚀 Guia de Deploy no Render

Este guia contém todas as instruções necessárias para fazer deploy do **SHIAI SISTEM** no Render.

## 📋 Pré-requisitos

1. Conta no [Render](https://render.com)
2. Repositório GitHub configurado
3. Branch `render-deploy` criada e com push realizado

## 🔧 Configuração no Render

### 1. Criar Novo Web Service

1. Acesse o [Dashboard do Render](https://dashboard.render.com)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte seu repositório GitHub: `vinicius-lier/shiai_sistem`
4. Selecione a branch: **`render-deploy`**

### 2. Configurações Básicas

**Nome do Serviço:**
```
shiai-sistem
```

**Região:**
```
Oregon (US West) ou São Paulo (se disponível)
```

**Branch:**
```
render-deploy
```

**Root Directory:**
```
(Deixe em branco - raiz do projeto)
```

**Runtime:**
```
Python 3
```

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn judocomp.wsgi
```

### 3. Variáveis de Ambiente

Adicione as seguintes variáveis de ambiente no Render:

| Variável | Valor | Descrição |
|----------|-------|-----------|
| `SECRET_KEY` | `[GERAR CHAVE SEGURA]` | Chave secreta do Django (veja abaixo como gerar) |
| `DEBUG` | `False` | Modo debug desativado em produção |
| `RENDER` | `true` | Indica que está rodando no Render |
| `SENHA_OPERACIONAL` | `[SUA SENHA]` | Senha para acesso ao módulo operacional |
| `RESET_ADMIN_PASSWORD` | `[OPCIONAL]` | Senha para reset do admin (opcional) |

#### Como Gerar SECRET_KEY:

Execute no terminal:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Ou use este comando Python:
```python
import secrets
print(secrets.token_urlsafe(50))
```

### 4. Configuração de Disco Persistente

O Render oferece disco persistente para armazenar o banco de dados SQLite:

1. No painel do serviço, vá em **"Disk"**
2. Clique em **"Mount Disk"**
3. Configure:
   - **Mount Path:** `/var/data`
   - **Size:** `1GB` (ou mais, conforme necessário)

⚠️ **Importante:** O banco de dados será salvo em `/var/data/db.sqlite3` no Render.

### 5. Configurações Avançadas

**Health Check Path:**
```
/
```

**Auto-Deploy:**
```
Yes (deploy automático quando houver push na branch)
```

## 📦 Estrutura de Arquivos

O projeto já está configurado com:

- ✅ `Procfile` - Define o comando de start
- ✅ `requirements.txt` - Dependências Python
- ✅ `settings.py` - Configurado para Render
- ✅ WhiteNoise - Para servir arquivos estáticos
- ✅ Banco de dados - SQLite em disco persistente

## 🔄 Processo de Deploy

1. **Build:** Render instala dependências e executa migrações
2. **Collectstatic:** Coleta todos os arquivos estáticos
3. **Start:** Inicia o servidor Gunicorn

## ✅ Verificação Pós-Deploy

Após o deploy, verifique:

1. **Acesso ao site:** `https://seu-app.onrender.com`
2. **Admin Django:** `https://seu-app.onrender.com/admin`
3. **Arquivos estáticos:** Verifique se CSS/JS estão carregando
4. **Banco de dados:** Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```

## 🛠️ Comandos Úteis no Render

### Shell do Render

No painel do serviço, você pode abrir um shell para executar comandos Django:

```bash
# Criar superusuário
python manage.py createsuperuser

# Criar usuário operacional
python manage.py criar_usuario_principal --username admin --password SUA_SENHA

# Aplicar migrações manualmente
python manage.py migrate

# Popular dados de teste
python manage.py seed_test_data
```

## 🔒 Segurança

### Configurações de Produção

O `settings.py` já está configurado para:
- ✅ `DEBUG=False` em produção
- ✅ `SECRET_KEY` via variável de ambiente
- ✅ `ALLOWED_HOSTS` configurado para `.onrender.com`
- ✅ WhiteNoise para arquivos estáticos
- ✅ Sessões seguras configuradas

### Recomendações Adicionais

1. **HTTPS:** Render fornece HTTPS automaticamente
2. **SECRET_KEY:** Use uma chave forte e única
3. **Senhas:** Não commite senhas no código
4. **Backup:** Faça backup regular do banco de dados

## 🐛 Troubleshooting

### Erro: "DisallowedHost"

Verifique se `ALLOWED_HOSTS` inclui `.onrender.com`

### Erro: "Static files not found"

Execute manualmente:
```bash
python manage.py collectstatic --noinput
```

### Erro: "Database locked"

SQLite pode ter problemas com múltiplas conexões. Considere migrar para PostgreSQL em produção.

### Erro: "Module not found"

Verifique se todas as dependências estão no `requirements.txt`

## 📊 Monitoramento

O Render fornece:
- **Logs em tempo real**
- **Métricas de performance**
- **Status do serviço**

Acesse em: Dashboard → Seu Serviço → Logs

## 🔄 Atualizações

Para atualizar o sistema:

1. Faça alterações na branch `render-deploy`
2. Faça commit e push:
   ```bash
   git add .
   git commit -m "Sua mensagem"
   git push origin render-deploy
   ```
3. O Render fará deploy automático

## 📞 Suporte

- **Documentação Render:** https://render.com/docs
- **Django Deployment:** https://docs.djangoproject.com/en/stable/howto/deployment/

---

**Última atualização:** Dezembro 2025
**Branch:** `render-deploy`

