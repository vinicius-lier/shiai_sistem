# 🔧 Correção: Imagens nos Templates

## 📋 Problema Identificado

Os templates estavam usando caminhos hardcoded `/static/img/logo_*.png` ao invés de usar a tag `{% static %}` do Django. Isso causava:

- ❌ 404 em `/static/img/logo_white.png`
- ❌ Imagens não carregavam em produção
- ❌ Dependência de caminhos absolutos que não funcionam com WhiteNoise

## ✅ Solução Aplicada

Todos os templates foram corrigidos para usar `{% static 'img/logo_*.png' %}` ao invés de caminhos hardcoded.

### Arquivos Corrigidos:

1. ✅ `atletas/templates/atletas/base.html`
   - Favicon: `/static/img/logo_black.png` → `{% static 'img/logo_black.png' %}`
   - Navbar logo: `/static/img/logo_white.png` → `{% static 'img/logo_white.png' %}`
   - Sidebar logo: `/static/img/logo_white.png` → `{% static 'img/logo_white.png' %}`

2. ✅ `atletas/templates/atletas/academia/base_academia.html`
   - 2 ocorrências de `logo_white.png` corrigidas

3. ✅ `atletas/templates/atletas/login_operacional.html`
   - Logo corrigido

4. ✅ `atletas/templates/atletas/alterar_senha_obrigatorio.html`
   - Logo corrigido

5. ✅ `atletas/templates/atletas/academia/login.html`
   - Logo corrigido

6. ✅ `atletas/templates/atletas/academia/selecionar_login.html`
   - Logo corrigido

7. ✅ `atletas/templates/atletas/academia/painel.html`
   - 2 ocorrências corrigidas

8. ✅ `atletas/templates/atletas/academia/cadastrar_atleta.html`
   - 2 ocorrências corrigidas

9. ✅ `atletas/templates/atletas/academia/evento.html`
   - 2 ocorrências corrigidas

10. ✅ `atletas/templates/atletas/academia/lista_atletas.html`
    - 4 ocorrências corrigidas

11. ✅ `atletas/templates/atletas/academia/inscrever_atletas.html`
    - 2 ocorrências corrigidas

12. ✅ `atletas/templates/atletas/landing.html`
    - Logo corrigido

## 📊 Resultado

**Antes:**
```html
<img src="/static/img/logo_white.png" alt="SHIAI SISTEM">
```

**Depois:**
```html
<img src="{% static 'img/logo_white.png' %}" alt="SHIAI SISTEM">
```

## ✅ Benefícios

1. **Funciona com WhiteNoise**: A tag `{% static %}` resolve corretamente os caminhos em produção
2. **Funciona com collectstatic**: Os arquivos são coletados corretamente para `staticfiles/`
3. **Compatível com DEBUG=True e DEBUG=False**: Funciona em desenvolvimento e produção
4. **Manutenção mais fácil**: Se o caminho mudar, só precisa atualizar em um lugar

## 🔍 Verificação

Após o deploy, verifique:
- ✅ Logos aparecem corretamente em todas as páginas
- ✅ Não há mais 404 para `/static/img/logo_*.png`
- ✅ Imagens carregam tanto em desenvolvimento quanto em produção

## 📝 Nota sobre Media Files

Os arquivos de media (fotos de atletas/academias) estão em `/media/fotos/` e são servidos via:
- `judocomp/urls.py` - Configurado para servir media sempre (DEBUG ou RENDER)
- `settings.py` - MEDIA_ROOT aponta para `/var/data/media` no Render

Se houver 404 em media files, verifique:
1. Se os arquivos existem no disco persistente `/var/data/media`
2. Se a pasta foi criada durante o build
3. Se os arquivos foram enviados corretamente

---

**Total de correções:** 19 ocorrências em 12 arquivos
**Status:** ✅ Todos os templates corrigidos

