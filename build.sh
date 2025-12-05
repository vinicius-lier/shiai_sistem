#!/bin/bash
# Script de build para Render com PostgreSQL
# Este script é executado automaticamente pelo Render antes de iniciar o servidor

set -e  # Parar em caso de erro crítico

echo "🚀 Iniciando build do projeto Django para Render..."

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Aplicar migrations (PostgreSQL será usado se DATABASE_URL estiver configurado)
echo "🗄️  Aplicando migrations do banco de dados..."
# Usar --skip-checks para evitar verificação de banco durante build
python manage.py migrate --noinput --skip-checks || {
    echo "⚠️  Migrate com --skip-checks falhou, tentando sem --skip-checks..."
    python manage.py migrate --noinput || {
        echo "❌ ERRO: migrate falhou"
        exit 1
    }
}

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
if python manage.py collectstatic --noinput --clear --skip-checks; then
    echo "✅ collectstatic executado com sucesso"
else
    echo "⚠️  collectstatic com --skip-checks falhou, tentando sem --skip-checks..."
    if python manage.py collectstatic --noinput --clear; then
        echo "✅ collectstatic executado com sucesso"
    else
        echo "❌ ERRO ao executar collectstatic!"
        exit 1
    fi
fi

# Verificar se a pasta staticfiles foi criada
if [ ! -d "staticfiles" ]; then
    echo "❌ ERRO: Pasta staticfiles não foi criada!"
    exit 1
fi

# Verificar se os logos foram coletados
echo "🔍 Verificando se logos foram coletados..."
if [ -f "staticfiles/img/logo_white.png" ] && [ -f "staticfiles/img/logo_black.png" ]; then
    echo "✅ Logos coletados com sucesso"
else
    echo "⚠️  Aviso: Logos não encontrados em staticfiles/img/"
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
fi

echo "✅ Build concluído com sucesso!"
