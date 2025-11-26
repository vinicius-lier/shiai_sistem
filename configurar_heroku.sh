#!/bin/bash
# Script para configurar Heroku para o projeto SHIAI

echo "=== Configurando Heroku para SHIAI SISTEM ==="
echo ""

# 1. Verificar se Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI não encontrado. Instalando..."
    curl https://cli-assets.heroku.com/install.sh | sh
    echo "✅ Heroku CLI instalado!"
else
    echo "✅ Heroku CLI já está instalado"
    heroku --version
fi

echo ""
echo "=== Login no Heroku ==="
echo "Você será solicitado a fazer login no Heroku..."
heroku login

echo ""
echo "=== Configurando Git Remote ==="
cd /home/vinicius/Downloads/shiai_sistem-main

# Verificar se já existe remote do Heroku
if git remote | grep -q heroku; then
    echo "✅ Remote do Heroku já configurado"
    git remote -v | grep heroku
else
    echo "📝 Adicionando remote do Heroku..."
    # Se já tem um app criado, use: heroku git:remote -a nome-do-app
    # Se não tem, crie um novo: heroku create
    echo "Escolha uma opção:"
    echo "1. Criar novo app no Heroku"
    echo "2. Conectar a app existente"
    read -p "Opção (1 ou 2): " opcao
    
    if [ "$opcao" = "1" ]; then
        heroku create shiai-sistem
    elif [ "$opcao" = "2" ]; then
        read -p "Digite o nome do app Heroku: " app_name
        heroku git:remote -a "$app_name"
    fi
fi

echo ""
echo "=== Configurando Variáveis de Ambiente ==="
echo "Configurando variáveis essenciais..."

# Gerar SECRET_KEY se não existir
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

heroku config:set SECRET_KEY="$SECRET_KEY"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="shiai-sistem-a1f98abf96a1.herokuapp.com,*.herokuapp.com"

echo ""
echo "=== Adicionando PostgreSQL ==="
echo "Adicionando addon PostgreSQL (plano gratuito)..."
heroku addons:create heroku-postgresql:mini

echo ""
echo "=== Fazendo Deploy ==="
echo "Enviando código para o Heroku..."
git push heroku main

echo ""
echo "=== Executando Migrations ==="
echo "Aplicando migrations no banco de dados..."
heroku run python manage.py migrate

echo ""
echo "=== Criando Superusuário ==="
echo "Você será solicitado a criar um superusuário..."
heroku run python manage.py createsuperuser

echo ""
echo "=== Verificando Status ==="
heroku ps
heroku logs --tail

echo ""
echo "✅ Configuração concluída!"
echo "🌐 Seu app está disponível em: https://$(heroku apps:info | grep 'Web URL' | awk '{print $3}')"

