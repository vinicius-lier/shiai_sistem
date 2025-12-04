# 🔧 Configurar Build Command no Render

## ⚠️ Problema Identificado

Os logs mostram:
```
No directory at: /opt/render/project/src/staticfiles/
GET /static/img/logo_white.png HTTP/1.1" 404
```

Isso indica que o `collectstatic` **não está sendo executado** durante o build.

## ✅ Solução: Configurar Build Command

### Passo 1: Acessar Configurações do Render

1. Acesse: https://dashboard.render.com
2. Selecione seu serviço: **shiai-sistem**
3. Vá em **Settings** → **Build & Deploy**

### Passo 2: Configurar Build Command

**Opção A: Usar build.sh (Recomendado)**

```bash
chmod +x build.sh && ./build.sh
```

**Opção B: Build Command Manual**

```bash
pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear
```

### Passo 3: Verificar Start Command

O **Start Command** deve ser:
```bash
gunicorn judocomp.wsgi --config gunicorn.conf.py
```

Ou simplesmente:
```bash
gunicorn judocomp.wsgi
```

## 🔍 Verificação

Após configurar e fazer deploy, verifique os logs:

1. **Durante o Build**, você deve ver:
   ```
   📁 Coletando arquivos estáticos...
   ✅ collectstatic executado com sucesso
   ✅ Logos coletados com sucesso em staticfiles/img/
   ```

2. **No Startup**, você NÃO deve ver:
   ```
   ❌ No directory at: /opt/render/project/src/staticfiles/
   ```

3. **Acessando o site**, você NÃO deve ver:
   ```
   ❌ GET /static/img/logo_white.png HTTP/1.1" 404
   ```

## 🛠️ Troubleshooting

### Se o build.sh não funcionar:

1. Verifique se o arquivo existe no repositório
2. Verifique se tem permissão de execução (deve ter `chmod +x`)
3. Use a Opção B (Build Command Manual) como alternativa

### Se collectstatic falhar:

Execute manualmente no shell do Render:
```bash
python manage.py collectstatic --noinput --clear
ls -la staticfiles/img/logo_*.png
```

### Se a pasta staticfiles não persistir:

O problema pode ser que o build está executando em um container temporário. Certifique-se de que:
- O Build Command está configurado corretamente
- O `collectstatic` está sendo executado **antes** do servidor iniciar
- Não há erros silenciosos no build

## 📝 Checklist

- [ ] Build Command configurado no Render
- [ ] Build Command inclui `collectstatic --noinput --clear`
- [ ] Start Command configurado corretamente
- [ ] Deploy realizado após configuração
- [ ] Logs do build mostram collectstatic executado
- [ ] Logs do startup não mostram warning sobre staticfiles
- [ ] Arquivos estáticos carregam corretamente no site

## 🚀 Próximos Passos

1. ✅ Configurar Build Command no Render
2. ✅ Fazer novo deploy
3. ✅ Verificar logs do build
4. ✅ Testar acesso aos arquivos estáticos

---

**Última atualização:** Dezembro 2024

