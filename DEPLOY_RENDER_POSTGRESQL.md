# 🚀 Deploy no Render com PostgreSQL - Guia Completo

## 📋 Pré-requisitos

- Conta no Render: https://render.com
- Repositório Git configurado
- Branch `postgresql-migration` criada

## 🔧 Configuração Passo a Passo

### 1. Criar Banco de Dados PostgreSQL

1. Acesse: https://dashboard.render.com
2. Clique em **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `shiai-database`
   - **Database**: `shiai_db`
   - **Region**: Mesma região do serviço web
   - **PostgreSQL Version**: 15 ou superior
   - **Plan**: Escolha conforme necessidade
4. Clique em **Create Database**

### 2. Obter DATABASE_URL

1. Acesse o banco criado
2. Na seção **Connections**, copie a **Internal Database URL**
3. Formato: `postgresql://user:password@host:port/database`

### 3. Criar Serviço Web

1. Clique em **New +** → **Web Service**
2. Conecte seu repositório Git
3. Configure:
   - **Name**: `shiai-sistem`
   - **Region**: Mesma do banco
   - **Branch**: `postgresql-migration`
   - **Root Directory**: (deixe vazio ou `/` se necessário)
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python manage.py migrate --noinput --skip-checks && python manage.py collectstatic --noinput --clear --skip-checks
     ```
   - **Start Command**: 
     ```bash
     gunicorn judocomp.wsgi --config gunicorn.conf.py
     ```

### 4. Configurar Variáveis de Ambiente

No serviço web, vá em **Environment** e adicione:

#### Obrigatórias:
- `DATABASE_URL`: Cole a URL do PostgreSQL (Internal Database URL)
- `SECRET_KEY`: Gere uma chave secreta (ex: `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
- `DEBUG`: `False` (produção)
- `SENHA_OPERACIONAL`: Senha para acesso operacional

#### Opcionais:
- `ALLOWED_HOSTS`: `shiai-sistem.onrender.com` (se necessário)

### 5. Vincular Banco ao Serviço Web

1. No painel do PostgreSQL
2. Vá em **Connections**
3. Em **Private Networking**, adicione seu serviço web
4. Isso permite conexão mais rápida e segura

### 6. Fazer Deploy

1. Clique em **Manual Deploy** → **Deploy latest commit**
2. Aguarde o build completar
3. Verifique os logs

## ✅ Verificação

### Durante o Build:
- ✅ Dependências instaladas
- ✅ Migrations aplicadas
- ✅ Arquivos estáticos coletados

### Durante o Runtime:
- ✅ Servidor inicia sem erros
- ✅ Conexão com PostgreSQL estabelecida
- ✅ Páginas carregam corretamente

## 🔍 Troubleshooting

### Erro: "could not connect to server"
**Solução:** Verifique se `DATABASE_URL` está correto e se o serviço está vinculado ao banco.

### Erro: "relation does not exist"
**Solução:** Execute `python manage.py migrate` no Shell do Render.

### Erro: "static files not found"
**Solução:** Verifique se `collectstatic` foi executado durante o build.

## 📊 Estrutura de Arquivos

```
shiai_sistem/
├── judocomp/
│   └── settings.py          # Configurado para PostgreSQL
├── build.sh                 # Script de build simplificado
├── Procfile                 # Comando de start
├── gunicorn.conf.py         # Configuração do Gunicorn
├── requirements.txt         # Dependências (inclui psycopg2-binary)
└── BUILD_COMMAND_RENDER.txt # Comando de build
```

## 🎯 Configurações Aplicadas

- ✅ PostgreSQL via `dj_database_url`
- ✅ SQLite apenas em desenvolvimento local
- ✅ WhiteNoise para arquivos estáticos
- ✅ Build command simplificado
- ✅ Start command configurado
- ✅ Media files em `/var/data/media`

---

**Projeto pronto para deploy no Render com PostgreSQL!**

