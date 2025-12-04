# 🚨 URGENTE: Configurar Build Command no Render

## ⚠️ Problema Atual

O deploy está falhando com o erro:
```
mkdir: cannot create directory '/var/data': Read-only file system
```

**Causa:** O `/var/data` não está disponível durante o build, apenas no runtime. Não podemos criar o banco durante o build.

## ✅ Solução

### Passo 1: Acessar Configurações do Render

1. Acesse: https://dashboard.render.com
2. Selecione seu serviço: **shiai-sistem**
3. Vá em **Settings** → **Build & Deploy**

### Passo 2: Configurar Build Command

**COPIE E COLE ESTE COMANDO no campo "Build Command":**

```bash
pip install -r requirements.txt && python manage.py migrate --noinput --skip-checks && python manage.py collectstatic --noinput --clear --skip-checks
```

### Passo 3: Salvar e Fazer Deploy

1. Clique em **Save Changes**
2. O Render fará um novo deploy automaticamente
3. Aguarde o build completar

## 🔍 Como Funciona

1. **Durante o Build:**
   - Instala dependências
   - Executa `migrate` com `--skip-checks` (não tenta acessar o banco)
   - Coleta arquivos estáticos com `--skip-checks`

2. **Durante o Runtime (quando o servidor inicia):**
   - O Django cria automaticamente o arquivo `/var/data/db.sqlite3` se não existir
   - As migrations serão aplicadas automaticamente na primeira requisição se necessário

## ⚠️ Por que `--skip-checks`?

O Django executa verificações automáticas (`check`) que tentam acessar o banco. Como o banco não existe durante o build, usamos `--skip-checks` para evitar essas verificações.

## 📋 O que o Comando Faz

1. **Instala dependências** Python
2. **Aplica migrations** com `--skip-checks` (não tenta acessar o banco)
3. **Coleta arquivos estáticos** com `--skip-checks`

---

**O banco será criado automaticamente quando o Django iniciar no runtime!**
