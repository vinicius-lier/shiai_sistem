# 🐘 Configurar PostgreSQL no Render

## 📋 Pré-requisitos

As dependências já estão instaladas no `requirements.txt`:
- `psycopg2-binary==2.9.11`
- `dj-database-url==3.0.1`

## 🚀 Passo a Passo

### 1. Criar Banco de Dados PostgreSQL no Render

1. Acesse: https://dashboard.render.com
2. Clique em **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `shiai-database` (ou outro nome de sua preferência)
   - **Database**: `shiai_db` (ou outro nome)
   - **User**: Será gerado automaticamente
   - **Region**: Escolha a mesma região do seu serviço web
   - **PostgreSQL Version**: 15 ou superior (recomendado)
   - **Plan**: Escolha o plano adequado (Free tier disponível)
4. Clique em **Create Database**

### 2. Obter String de Conexão (DATABASE_URL)

Após criar o banco:

1. Acesse o banco de dados criado no painel do Render
2. Na seção **Connections**, você verá a **Internal Database URL**
3. Copie essa URL (formato: `postgresql://user:password@host:port/database`)

### 3. Configurar Variável de Ambiente no Serviço Web

1. Acesse seu serviço web: **shiai-sistem**
2. Vá em **Environment**
3. Clique em **Add Environment Variable**
4. Configure:
   - **Key**: `DATABASE_URL`
   - **Value**: Cole a URL copiada do passo anterior
5. Clique em **Save Changes**

### 4. Vincular Banco ao Serviço Web (Opcional mas Recomendado)

1. No painel do banco de dados PostgreSQL
2. Vá em **Connections**
3. Em **Private Networking**, adicione seu serviço web
4. Isso permite conexão mais rápida e segura

### 5. Atualizar Build Command (Opcional)

O Build Command atual já funciona com PostgreSQL:
```bash
pip install -r requirements.txt && python manage.py migrate --noinput --skip-checks && python manage.py collectstatic --noinput --clear --skip-checks
```

### 6. Fazer Deploy

1. O Render fará deploy automaticamente após salvar a variável de ambiente
2. Ou dispare manualmente um novo deploy

## ✅ Verificação

Após o deploy, verifique os logs:

1. **Durante o Build:**
   - Deve ver: `Applying migrations...`
   - Não deve ver erros de conexão

2. **Durante o Runtime:**
   - Acesse o sistema
   - Verifique se as páginas carregam corretamente
   - Teste criar um registro (ex: categoria, academia)

## 🔍 Troubleshooting

### Erro: "could not connect to server"

**Causa:** O serviço web não está vinculado ao banco ou a URL está incorreta.

**Solução:**
1. Verifique se a variável `DATABASE_URL` está configurada corretamente
2. Verifique se o banco está na mesma região do serviço web
3. Vincule o serviço web ao banco em **Connections** → **Private Networking**

### Erro: "relation does not exist"

**Causa:** As migrations não foram aplicadas.

**Solução:**
1. Execute manualmente no Shell do Render:
   ```bash
   python manage.py migrate
   ```

### Erro: "permission denied"

**Causa:** O usuário do banco não tem permissões.

**Solução:**
1. Verifique se o usuário tem permissões no banco
2. Recrie o banco se necessário

## 📊 Vantagens do PostgreSQL

- ✅ Melhor performance para grandes volumes de dados
- ✅ Suporte a transações complexas
- ✅ Backup automático no Render
- ✅ Escalabilidade
- ✅ Melhor para produção

## 🔄 Migração de Dados (Se já tiver dados em SQLite)

Se você já tem dados no SQLite e quer migrar:

1. **Fazer backup do SQLite:**
   ```bash
   # No servidor Render (via Shell)
   cp /var/data/db.sqlite3 /var/data/db.sqlite3.backup
   ```

2. **Exportar dados:**
   ```bash
   python manage.py dumpdata > backup.json
   ```

3. **Configurar PostgreSQL** (seguir passos acima)

4. **Aplicar migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Importar dados:**
   ```bash
   python manage.py loaddata backup.json
   ```

---

**Após configurar, o sistema usará PostgreSQL automaticamente no Render!**

