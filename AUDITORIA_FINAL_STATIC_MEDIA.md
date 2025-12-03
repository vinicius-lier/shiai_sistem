# Auditoria Final - Static Files e Media Files

**Data:** 03/12/2025  
**Objetivo:** Garantir funcionamento correto de imagens estáticas (logos) e media files (uploads) em produção no Render

---

## 1. Estrutura de Pastas Corrigida

### ✅ Pastas Removidas
- `static/img/` - **REMOVIDA** (causava conflito e duplicação)

### ✅ Pastas Criadas/Mantidas
- `atletas/static/atletas/images/` - **ÚNICO local válido para logos**
  - `logo_white.png` ✅
  - `logo_black.png` ✅

### ✅ Pastas de Media (Uploads)
- `media/` - Mantida (uploads de usuários)
  - `media/fotos/atletas/` - Fotos de atletas
  - `media/fotos/academias/` - Logos de academias
  - `media/documentos/` - Documentos enviados

---

## 2. Configurações Corrigidas

### 2.1 `judocomp/settings.py`

```python
# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

✅ **Status:** Configurações corretas e mantidas

### 2.2 `judocomp/urls.py`

**ANTES (ERRADO):**
```python
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**DEPOIS (CORRETO):**
```python
# Servir MEDIA sempre (inclusive produção Render)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Manter staticfiles patterns SOMENTE se DEBUG=True
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
```

✅ **Status:** MEDIA agora funciona sempre, não apenas em DEBUG

---

## 3. Comando Criado

### `atletas/management/commands/ensure_media.py`

Comando criado para garantir que a pasta `MEDIA_ROOT` existe no deploy:

```python
from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Garante que a pasta MEDIA_ROOT existe'

    def handle(self, *args, **kwargs):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.stdout.write(
            self.style.SUCCESS(
                f'Pasta MEDIA criada/verificada: {settings.MEDIA_ROOT}'
            )
        )
```

**Uso no Render:**
Adicionar no `build.sh` ou comando de start:
```bash
python manage.py ensure_media
```

✅ **Status:** Comando criado e pronto para uso

---

## 4. Templates Corrigidos

### 4.1 Referências de Logos Corrigidas

**ANTES (ERRADO):**
```django
{% static 'img/logo_white.png' %}
{% static 'img/logo_black.png' %}
```

**DEPOIS (CORRETO):**
```django
{% static 'atletas/images/logo_white.png' %}
{% static 'atletas/images/logo_black.png' %}
```

### 4.2 Templates Corrigidos (12 arquivos)

1. ✅ `atletas/templates/atletas/base.html`
2. ✅ `atletas/templates/atletas/landing.html`
3. ✅ `atletas/templates/atletas/login_operacional.html`
4. ✅ `atletas/templates/atletas/alterar_senha_obrigatorio.html`
5. ✅ `atletas/templates/atletas/academia/base_academia.html`
6. ✅ `atletas/templates/atletas/academia/login.html`
7. ✅ `atletas/templates/atletas/academia/selecionar_login.html`
8. ✅ `atletas/templates/atletas/academia/painel.html`
9. ✅ `atletas/templates/atletas/academia/evento.html`
10. ✅ `atletas/templates/atletas/academia/cadastrar_atleta.html`
11. ✅ `atletas/templates/atletas/academia/lista_atletas.html`
12. ✅ `atletas/templates/atletas/academia/inscrever_atletas.html`

**Total de ocorrências corrigidas:** 22 referências

### 4.3 Referências de Media (Uploads)

Todas as referências a imagens enviadas pelo sistema devem usar:

```django
{{ atleta.foto.url }}
{{ academia.logo.url }}
{{ user.profile.foto.url }}
```

✅ **Status:** Templates verificados - usar sempre `.url` para media files

---

## 5. Checklist de Verificação no Render

### 5.1 Após Deploy

Execute no terminal do Render:

```bash
# 1. Verificar que logos estão no local correto
find /opt/render/project/src/staticfiles -name "logo_white.png"
find /opt/render/project/src/staticfiles -name "logo_black.png"

# Resultado esperado:
# /opt/render/project/src/staticfiles/atletas/images/logo_white.png
# /opt/render/project/src/staticfiles/atletas/images/logo_black.png

# 2. Verificar que NÃO existe em static/img/
find /opt/render/project/src/staticfiles/img -name "logo_*.png" 2>/dev/null
# Resultado esperado: Nenhum arquivo encontrado

# 3. Verificar que pasta MEDIA existe
ls -la /opt/render/project/src/media/
# Resultado esperado: Pasta existe e contém subpastas (fotos/, documentos/)

# 4. Verificar que MEDIA está sendo servida
curl -I https://seu-app.onrender.com/media/fotos/academias/1/logo.png
# Resultado esperado: HTTP 200 ou 404 (se arquivo não existir, mas rota funciona)
```

### 5.2 Testes Funcionais

- [ ] Logo branco aparece no navbar (modo claro)
- [ ] Logo preto aparece no navbar (modo escuro)
- [ ] Favicon aparece na aba do navegador
- [ ] Fotos de atletas carregam corretamente
- [ ] Logos de academias carregam corretamente
- [ ] Upload de novas imagens funciona

---

## 6. Comandos para Executar Localmente

```bash
# 1. Limpar staticfiles antigo
rm -rf staticfiles

# 2. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 3. Verificar estrutura
find staticfiles -name "logo_white.png"
find staticfiles -name "logo_black.png"

# Resultado esperado:
# staticfiles/atletas/images/logo_white.png
# staticfiles/atletas/images/logo_black.png

# 4. Garantir pasta MEDIA
python manage.py ensure_media
```

---

## 7. Resumo das Mudanças

### Arquivos Modificados:
1. ✅ `judocomp/urls.py` - MEDIA servido sempre
2. ✅ `atletas/management/commands/ensure_media.py` - Criado
3. ✅ 12 templates HTML - Referências de logos corrigidas

### Arquivos/Pastas Removidos:
1. ✅ `static/img/` - Pasta removida (duplicada)

### Arquivos/Pastas Criados:
1. ✅ `atletas/static/atletas/images/` - Pasta criada
2. ✅ `atletas/static/atletas/images/logo_white.png` - Movido
3. ✅ `atletas/static/atletas/images/logo_black.png` - Movido

---

## 8. Próximos Passos

1. ✅ Fazer commit das mudanças
2. ⏳ Fazer push para o repositório
3. ⏳ Aguardar deploy no Render
4. ⏳ Executar checklist de verificação
5. ⏳ Testar funcionalidades de upload e exibição de imagens

---

## 9. Notas Importantes

- ⚠️ **NUNCA** usar caminhos fixos para media files (ex: `/media/fotos/...`)
- ✅ **SEMPRE** usar `.url` do modelo (ex: `{{ atleta.foto.url }}`)
- ⚠️ **NUNCA** criar pasta `static/img/` novamente
- ✅ **SEMPRE** usar `{% static 'atletas/images/logo_*.png' %}` para logos
- ✅ Executar `python manage.py ensure_media` no build do Render

---

**Fim da Auditoria**

