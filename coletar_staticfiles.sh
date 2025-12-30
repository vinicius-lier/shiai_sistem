#!/bin/bash
# Script para coletar arquivos estáticos no Render
# Execute este script no shell do Render se staticfiles não existir

set -e

echo "=========================================="
echo "COLETANDO ARQUIVOS ESTÁTICOS"
echo "=========================================="
echo ""

# Verificar se estamos no Render
if [ -n "$RENDER" ]; then
    echo "✅ Ambiente Render detectado"
else
    echo "⚠️  Ambiente local (não é Render)"
fi

echo ""
echo "1. VERIFICANDO CONFIGURAÇÃO"
echo "-------------------------------------------"
python manage.py shell << 'PYTHON_EOF'
from django.conf import settings
import os
print("STATIC_ROOT:", settings.STATIC_ROOT)
print("STATIC_URL:", settings.STATIC_URL)
print("STATICFILES_DIRS:", settings.STATICFILES_DIRS)
print("STATICFILES_STORAGE:", settings.STATICFILES_STORAGE)
PYTHON_EOF

echo ""
echo "2. VERIFICANDO ARQUIVOS ORIGINAIS"
echo "-------------------------------------------"
if [ -f "static/img/logo_white.png" ]; then
    echo "✅ logo_white.png existe em static/img/"
    ls -lh static/img/logo_white.png
else
    echo "❌ logo_white.png NÃO encontrado em static/img/"
    exit 1
fi

if [ -f "static/img/logo_black.png" ]; then
    echo "✅ logo_black.png existe em static/img/"
    ls -lh static/img/logo_black.png
else
    echo "❌ logo_black.png NÃO encontrado em static/img/"
    exit 1
fi

echo ""
echo "3. EXECUTANDO COLECTSTATIC"
echo "-------------------------------------------"
python manage.py collectstatic --noinput --clear

echo ""
echo "4. VERIFICANDO SE OS ARQUIVOS FORAM COLETADOS"
echo "-------------------------------------------"
if [ -f "staticfiles/img/logo_white.png" ]; then
    echo "✅ logo_white.png coletado com sucesso!"
    ls -lh staticfiles/img/logo_white.png
else
    echo "❌ logo_white.png NÃO foi coletado"
    echo "📁 Conteúdo de staticfiles/:"
    ls -la staticfiles/ 2>/dev/null | head -10
    exit 1
fi

if [ -f "staticfiles/img/logo_black.png" ]; then
    echo "✅ logo_black.png coletado com sucesso!"
    ls -lh staticfiles/img/logo_black.png
else
    echo "❌ logo_black.png NÃO foi coletado"
    exit 1
fi

echo ""
echo "5. ESTRUTURA FINAL DE STATICFILES"
echo "-------------------------------------------"
echo "Total de arquivos em staticfiles/img/:"
find staticfiles/img -type f | wc -l
echo ""
echo "Arquivos PNG em staticfiles/img/:"
find staticfiles/img -name "*.png" | head -10

echo ""
echo "=========================================="
echo "✅ COLECTSTATIC CONCLUÍDO COM SUCESSO!"
echo "=========================================="

