# 🚨 URGENTE: Configurar Build Command no Render

## ⚠️ Problema Atual

O deploy está falhando com o erro:
```
sqlite3.OperationalError: unable to open database file
```

**Causa:** O Build Command no Render não está criando o arquivo do banco ANTES de executar comandos Django.

## ✅ Solução Imediata

### Passo 1: Acessar Configurações do Render

1. Acesse: https://dashboard.render.com
2. Selecione seu serviço: **shiai-sistem**
3. Vá em **Settings** → **Build & Deploy**

### Passo 2: Configurar Build Command

**COPIE E COLE ESTE COMANDO COMPLETO no campo "Build Command":**

```bash
mkdir -p /var/data && chmod 755 /var/data && touch /var/data/db.sqlite3 && chmod 644 /var/data/db.sqlite3 && pip install -r requirements.txt && python manage.py migrate --noinput --run-syncdb --skip-checks && python manage.py collectstatic --noinput --clear --skip-checks
```

**OU use o build.sh:**

```bash
chmod +x build.sh && ./build.sh
```

### Passo 3: Salvar e Fazer Deploy

1. Clique em **Save Changes**
2. O Render fará um novo deploy automaticamente
3. Aguarde o build completar

## 🔍 Como Verificar se Funcionou

### Durante o Build, você deve ver nos logs:

```
✅ Arquivo /var/data/db.sqlite3 criado/verificado com sucesso
📦 Instalando dependências Python...
🗄️  Aplicando migrations do banco de dados...
✅ collectstatic executado com sucesso
✅ Build concluído com sucesso!
```

### Você NÃO deve ver:

```
❌ sqlite3.OperationalError: unable to open database file
❌ Build failed 😞
```

## 📋 O que o Comando Faz

1. **Cria a pasta `/var/data`** com permissões corretas
2. **Cria o arquivo `/var/data/db.sqlite3`** vazio (CRÍTICO - deve ser primeiro!)
3. **Instala dependências** Python
4. **Aplica migrations** com `--skip-checks` para evitar verificação de banco
5. **Coleta arquivos estáticos** com `--skip-checks`

## ⚠️ Por que `--skip-checks`?

O Django executa verificações automáticas (`check`) que tentam acessar o banco durante o import. O `--skip-checks` evita essas verificações durante o build, permitindo que o arquivo do banco seja criado primeiro.

## 🎯 Próximos Passos

Após configurar o Build Command:
1. Aguarde o deploy completar
2. Verifique os logs do build
3. Teste o acesso ao sistema

---

**Este é o último passo necessário para resolver o erro de deploy!**

