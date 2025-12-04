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

