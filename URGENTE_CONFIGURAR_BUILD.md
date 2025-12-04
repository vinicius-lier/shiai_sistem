# 🚨 URGENTE: Configurar Build Command no Render

## ⚠️ Problema Atual

Os logs do Render mostram:
- ❌ `No directory at: /opt/render/project/src/staticfiles/`
- ❌ `GET /static/img/logo_white.png HTTP/1.1" 404`

**Causa:** O `collectstatic` **NÃO está sendo executado** durante o build.

## ✅ Solução Imediata

### No Painel do Render:

1. **Acesse:** https://dashboard.render.com → Seu serviço → **Settings** → **Build & Deploy**

2. **Configure o Build Command:**
   ```bash
   chmod +x build.sh && ./build.sh
   ```

3. **OU use este comando direto:**
   ```bash
   mkdir -p /var/data && chmod -R 755 /var/data && touch /var/data/db.sqlite3 && chmod 644 /var/data/db.sqlite3 && pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear
   ```

⚠️ **CRÍTICO:** A pasta `/var/data` e o arquivo do banco DEEM ser criados PRIMEIRO, antes de qualquer comando Django!

4. **Salve e faça um novo deploy**

## 🔍 Como Verificar se Funcionou

Após o deploy, nos logs do **Build** você deve ver:
```
📁 Coletando arquivos estáticos...
✅ collectstatic executado com sucesso
✅ Logos coletados com sucesso em staticfiles/img/
```

E nos logs do **Runtime** você NÃO deve ver:
```
❌ No directory at: /opt/render/project/src/staticfiles/
```

## 📋 Status Atual

- ✅ Migration 0036 corrigida (usando classe_id)
- ✅ build.sh criado e funcional
- ✅ WhiteNoise configurado corretamente
- ❌ **Build Command não configurado no Render** ← **AÇÃO NECESSÁRIA**

## 🎯 Próxima Ação

**VOCÊ PRECISA:**
1. Acessar o painel do Render
2. Configurar o Build Command (usar um dos comandos acima)
3. Fazer um novo deploy
4. Verificar se os arquivos estáticos carregam

---

**Este é o último passo necessário para resolver o problema de 404 nos arquivos estáticos!**

