#!/bin/bash
# Script para verificar e corrigir problemas de static files no Render

echo "=== VERIFICAÇÃO DETALHADA ==="
echo ""

echo "1. Verificando se arquivos existem em static/img/"
echo "-------------------------------------------"
if [ -d "static/img" ]; then
    echo "✅ Pasta static/img existe"
    ls -la static/img/logo_*.png 2>/dev/null || echo "❌ Logos não encontrados em static/img/"
else
    echo "❌ Pasta static/img NÃO existe"
fi

echo ""
echo "2. Verificando STATICFILES_DIRS"
echo "-------------------------------------------"
python manage.py shell << 'PYTHON_EOF'
from django.conf import settings
import os
print("STATICFILES_DIRS:", settings.STATICFILES_DIRS)
for dir_path in settings.STATICFILES_DIRS:
    path_str = str(dir_path)
    exists = os.path.exists(path_str)
    print(f"  {path_str}: {'✅ existe' if exists else '❌ NÃO existe'}")
    if exists and os.path.isdir(path_str):
        img_path = os.path.join(path_str, 'img')
        print(f"    static/img: {'✅ existe' if os.path.exists(img_path) else '❌ NÃO existe'}")
PYTHON_EOF

echo ""
echo "3. Testando findstatic"
echo "-------------------------------------------"
python manage.py findstatic img/logo_white.png 2>&1

echo ""
echo "4. Testando collectstatic (dry-run)"
echo "-------------------------------------------"
python manage.py collectstatic --noinput --dry-run 2>&1 | grep -E "(img/logo|Copying.*img)" | head -10

echo ""
echo "5. Verificando estrutura de staticfiles após collectstatic"
echo "-------------------------------------------"
python manage.py collectstatic --noinput --clear 2>&1 | tail -5
echo ""
ls -la staticfiles/img/logo_*.png 2>/dev/null || echo "❌ Logos ainda não encontrados após collectstatic"

echo ""
echo "=== FIM DA VERIFICAÇÃO ==="

