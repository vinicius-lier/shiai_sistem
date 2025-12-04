#!/bin/bash
# Script de build para Render
# Este script é executado automaticamente pelo Render antes de iniciar o servidor

# NÃO usar set -e aqui porque queremos continuar mesmo se alguns comandos falharem
# set -e

echo "🚀 Iniciando build do projeto..."

# CRÍTICO: Criar pasta /var/data e arquivo do banco ANTES de qualquer comando Django
# O Django executa verificações automáticas que tentam acessar o banco
# Isso DEVE ser feito ANTES de qualquer import do Django
echo "📁 Criando pasta /var/data e arquivo do banco (CRÍTICO - deve ser primeiro)..."
if [ -n "$RENDER" ]; then
    # Criar diretório com permissões corretas
    mkdir -p /var/data
    chmod 755 /var/data
    
    # Criar arquivo do banco vazio ANTES de qualquer comando Python/Django
    # SQLite precisa que o arquivo exista para poder abri-lo
    touch /var/data/db.sqlite3
    chmod 644 /var/data/db.sqlite3
    
    # Verificar se foi criado
    if [ -f "/var/data/db.sqlite3" ]; then
        echo "✅ Arquivo /var/data/db.sqlite3 criado com sucesso"
        ls -lh /var/data/db.sqlite3
    else
        echo "❌ ERRO: Não foi possível criar /var/data/db.sqlite3"
        exit 1
    fi
    
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
# Garantir que o arquivo do banco existe antes de migrar
if [ -n "$RENDER" ]; then
    if [ ! -f "/var/data/db.sqlite3" ]; then
        echo "⚠️  Arquivo do banco não encontrado, criando novamente..."
        touch /var/data/db.sqlite3
        chmod 644 /var/data/db.sqlite3
    fi
    # Verificar permissões
    chmod 755 /var/data 2>/dev/null || true
    chmod 644 /var/data/db.sqlite3 2>/dev/null || true
    echo "📋 Verificando arquivo do banco:"
    ls -la /var/data/db.sqlite3 || echo "⚠️  Arquivo do banco não encontrado"
fi
# Usar --skip-checks para evitar verificação de banco durante migrate
echo "🔄 Executando migrate com --skip-checks..."
python manage.py migrate --noinput --run-syncdb --skip-checks 2>&1 || {
    echo "⚠️  Migrate com --skip-checks falhou, tentando sem --skip-checks..."
    python manage.py migrate --noinput --run-syncdb 2>&1 || {
        echo "❌ ERRO: migrate falhou completamente"
        exit 1
    }
}

# Verificar migrations pendentes
echo "🔍 Verificando migrations pendentes..."
python manage.py showmigrations --skip-checks 2>&1 | grep "\[ \]" || echo "✅ Todas as migrations aplicadas"

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
echo "   Verificando arquivos originais em static/img/:"
ls -la static/img/ 2>/dev/null | head -5 || echo "   ⚠️  Pasta static/img/ não encontrada"

# Executar collectstatic com verificação de erro
echo "📁 Executando collectstatic com --skip-checks..."
if python manage.py collectstatic --noinput --clear --skip-checks 2>&1; then
    echo "✅ collectstatic executado com sucesso"
else
    echo "⚠️  collectstatic com --skip-checks falhou, tentando sem --skip-checks..."
    if python manage.py collectstatic --noinput --clear 2>&1; then
        echo "✅ collectstatic executado com sucesso (sem --skip-checks)"
    else
        echo "❌ ERRO ao executar collectstatic!"
        echo "   Tentando novamente sem --clear..."
        python manage.py collectstatic --noinput 2>&1 || {
            echo "❌ ERRO CRÍTICO: collectstatic falhou!"
            exit 1
        }
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

