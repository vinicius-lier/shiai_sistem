#!/bin/bash
# Script de build para Render
# Este script é executado automaticamente pelo Render antes de iniciar o servidor

set -e  # Parar em caso de erro

echo "🚀 Iniciando build do projeto..."

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Aplicar migrations (forçar aplicação de todas)
echo "🗄️  Aplicando migrations do banco de dados..."
python manage.py migrate --noinput --run-syncdb

# Verificar migrations pendentes
echo "🔍 Verificando migrations pendentes..."
python manage.py showmigrations | grep "\[ \]" || echo "✅ Todas as migrations aplicadas"

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Verificar se os logos foram coletados
echo "🔍 Verificando se logos foram coletados..."
if [ -f "staticfiles/img/logo_white.png" ] && [ -f "staticfiles/img/logo_black.png" ]; then
    echo "✅ Logos coletados com sucesso em staticfiles/img/"
    ls -lh staticfiles/img/logo_*.png
else
    echo "⚠️  Aviso: Logos não encontrados em staticfiles/img/"
    echo "📁 Conteúdo de staticfiles/:"
    ls -la staticfiles/ 2>/dev/null | head -10
    echo "📁 Procurando logos em staticfiles:"
    find staticfiles -name "logo_*.png" 2>/dev/null || echo "Nenhum logo encontrado"
fi

# Garantir que a pasta media existe (importante para Render)
echo "📁 Garantindo que a pasta MEDIA existe..."
if [ -n "$RENDER" ]; then
    mkdir -p /var/data/media/fotos/academias
    mkdir -p /var/data/media/fotos/atletas
    mkdir -p /var/data/media/fotos/temp
    mkdir -p /var/data/media/documentos/temp
    mkdir -p /var/data/media/comprovantes
    chmod -R 755 /var/data/media
    echo "✅ Pasta /var/data/media e subpastas criadas"
else
    python manage.py ensure_media || true
fi

echo "✅ Build concluído com sucesso!"

