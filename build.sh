#!/bin/bash
# Script de build para Render
# Este script é executado automaticamente pelo Render antes de iniciar o servidor

set -e  # Parar em caso de erro

echo "🚀 Iniciando build do projeto..."

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Aplicar migrations
echo "🗄️  Aplicando migrations do banco de dados..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "✅ Build concluído com sucesso!"

