#!/bin/bash
# Script de diagnóstico para problemas de 404 em imagens no Render
# Execute este script no shell do Render

echo "=========================================="
echo "DIAGNÓSTICO DE 404 - ARQUIVOS ESTÁTICOS E MEDIA"
echo "=========================================="
echo ""

echo "1. VERIFICANDO ARQUIVOS ESTÁTICOS COLETADOS"
echo "-------------------------------------------"
if [ -f "staticfiles/img/logo_white.png" ]; then
    echo "✅ logo_white.png existe em staticfiles/img/"
    ls -lh staticfiles/img/logo_white.png
else
    echo "❌ logo_white.png NÃO encontrado em staticfiles/img/"
fi

if [ -f "staticfiles/img/logo_black.png" ]; then
    echo "✅ logo_black.png existe em staticfiles/img/"
    ls -lh staticfiles/img/logo_black.png
else
    echo "❌ logo_black.png NÃO encontrado em staticfiles/img/"
fi

echo ""
echo "2. ESTRUTURA DE STATICFILES"
echo "-------------------------------------------"
echo "Conteúdo de staticfiles/:"
ls -la staticfiles/ | head -10
echo ""
echo "Conteúdo de staticfiles/img/:"
ls -la staticfiles/img/ 2>/dev/null || echo "Pasta staticfiles/img/ não existe"

echo ""
echo "3. ARQUIVOS ORIGINAIS EM static/img/"
echo "-------------------------------------------"
ls -la static/img/ 2>/dev/null || echo "Pasta static/img/ não existe"

echo ""
echo "4. CONFIGURAÇÕES DO DJANGO"
echo "-------------------------------------------"
python manage.py shell << 'PYTHON_EOF'
from django.conf import settings
import os
print("STATIC_ROOT:", settings.STATIC_ROOT)
print("STATIC_URL:", settings.STATIC_URL)
print("STATICFILES_DIRS:", settings.STATICFILES_DIRS)
print("STATICFILES_STORAGE:", settings.STATICFILES_STORAGE)
print("MEDIA_ROOT:", settings.MEDIA_ROOT)
print("MEDIA_URL:", settings.MEDIA_URL)
print("DEBUG:", settings.DEBUG)
print("RENDER env:", os.environ.get("RENDER", "Não definido"))
PYTHON_EOF

echo ""
echo "5. VERIFICANDO WHITENOISE"
echo "-------------------------------------------"
pip show whitenoise | grep -E "(Name|Version)" || echo "WhiteNoise não instalado"
python manage.py shell << 'PYTHON_EOF'
from django.conf import settings
middleware_str = str(settings.MIDDLEWARE)
if 'whitenoise' in middleware_str.lower():
    print("✅ WhiteNoise está no MIDDLEWARE")
    # Encontrar posição
    for i, mw in enumerate(settings.MIDDLEWARE):
        if 'whitenoise' in mw.lower():
            print(f"   Posição: {i} - {mw}")
else:
    print("❌ WhiteNoise NÃO está no MIDDLEWARE")
PYTHON_EOF

echo ""
echo "6. TESTANDO FINDSTATIC"
echo "-------------------------------------------"
python manage.py findstatic img/logo_white.png 2>&1 || echo "Arquivo não encontrado pelo findstatic"

echo ""
echo "7. VERIFICANDO PASTA MEDIA"
echo "-------------------------------------------"
if [ -d "/var/data/media" ]; then
    echo "✅ Pasta /var/data/media existe"
    ls -la /var/data/media/ | head -10
    echo ""
    if [ -d "/var/data/media/fotos/academias" ]; then
        echo "✅ Pasta /var/data/media/fotos/academias existe"
        ls -la /var/data/media/fotos/academias/ | head -5
    else
        echo "❌ Pasta /var/data/media/fotos/academias NÃO existe"
    fi
else
    echo "❌ Pasta /var/data/media NÃO existe"
fi

echo ""
echo "8. VERIFICANDO VARIÁVEIS DE AMBIENTE"
echo "-------------------------------------------"
echo "RENDER: ${RENDER:-Não definido}"
echo "DEBUG: ${DEBUG:-Não definido}"

echo ""
echo "9. TESTANDO COLECTSTATIC"
echo "-------------------------------------------"
python manage.py collectstatic --noinput --dry-run 2>&1 | grep -E "(logo|img|Copying|staticfiles)" | head -10

echo ""
echo "=========================================="
echo "DIAGNÓSTICO CONCLUÍDO"
echo "=========================================="

