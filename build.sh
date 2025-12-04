#!/bin/bash
# Script de build para Render
# Este script é executado automaticamente pelo Render antes de iniciar o servidor

set -e  # Parar em caso de erro

echo "🚀 Iniciando build do projeto..."

# CRÍTICO: Criar pasta /var/data e arquivo do banco ANTES de qualquer comando Django
# O Django executa verificações automáticas que tentam acessar o banco
echo "📁 Criando pasta /var/data e arquivo do banco (CRÍTICO - deve ser primeiro)..."
if [ -n "$RENDER" ]; then
    mkdir -p /var/data
    chmod -R 755 /var/data
    # Criar arquivo do banco vazio para evitar erro durante verificações do Django
    touch /var/data/db.sqlite3
    chmod 644 /var/data/db.sqlite3
    echo "✅ Pasta /var/data e arquivo do banco criados"
else
    # Em desenvolvimento local, garantir que a pasta existe
    mkdir -p media
fi

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
echo "   Verificando arquivos originais em static/img/:"
ls -la static/img/ 2>/dev/null | head -5 || echo "   ⚠️  Pasta static/img/ não encontrada"

# Executar collectstatic com verificação de erro
if python manage.py collectstatic --noinput --clear; then
    echo "✅ collectstatic executado com sucesso"
else
    echo "❌ ERRO ao executar collectstatic!"
    echo "   Tentando novamente sem --clear..."
    python manage.py collectstatic --noinput || {
        echo "❌ ERRO CRÍTICO: collectstatic falhou!"
        exit 1
    }
fi

# Verificar se a pasta staticfiles foi criada
if [ ! -d "staticfiles" ]; then
    echo "❌ ERRO: Pasta staticfiles não foi criada!"
    exit 1
fi

# Verificar se os logos foram coletados
echo "🔍 Verificando se logos foram coletados..."
if [ -f "staticfiles/img/logo_white.png" ] && [ -f "staticfiles/img/logo_black.png" ]; then
    echo "✅ Logos coletados com sucesso em staticfiles/img/"
    ls -lh staticfiles/img/logo_*.png
    echo "   Total de arquivos em staticfiles/img/:"
    find staticfiles/img -type f | wc -l
else
    echo "⚠️  Aviso: Logos não encontrados em staticfiles/img/"
    echo "📁 Conteúdo de staticfiles/:"
    ls -la staticfiles/ 2>/dev/null | head -10
    echo "📁 Procurando logos em staticfiles:"
    find staticfiles -name "logo_*.png" 2>/dev/null || echo "Nenhum logo encontrado"
    echo "⚠️  Continuando build mesmo sem logos (pode ser problema de configuração)"
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

