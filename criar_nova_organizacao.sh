#!/bin/bash
# Script para criar uma nova organização completa
# Uso: ./criar_nova_organizacao.sh "Nome Org" "email@org.com" "(11) 98765-4321" "username" "senha123" "user@email.com"

set -e

if [ $# -lt 6 ]; then
    echo "❌ Erro: Parâmetros insuficientes"
    echo ""
    echo "Uso: $0 \"Nome da Organização\" \"email@org.com\" \"(11) 98765-4321\" \"username\" \"senha123\" \"user@email.com\""
    echo ""
    echo "Exemplo:"
    echo "  $0 \"Federação Paulista de Judô\" \"contato@fpj.com.br\" \"(11) 98765-4321\" \"organizador_fpj\" \"SenhaSegura123!\" \"admin@fpj.com.br\""
    exit 1
fi

ORGANIZACAO_NOME="$1"
ORGANIZACAO_EMAIL="$2"
ORGANIZACAO_TELEFONE="$3"
USUARIO_USERNAME="$4"
USUARIO_PASSWORD="$5"
USUARIO_EMAIL="$6"

echo "🚀 Criando nova organização..."
echo ""
echo "📋 Dados da Organização:"
echo "   Nome: $ORGANIZACAO_NOME"
echo "   Email: $ORGANIZACAO_EMAIL"
echo "   Telefone: $ORGANIZACAO_TELEFONE"
echo ""
echo "👤 Dados do Usuário:"
echo "   Username: $USUARIO_USERNAME"
echo "   Email: $USUARIO_EMAIL"
echo ""

# Criar organizador
echo "1️⃣  Criando organizador..."
python manage.py criar_organizador \
  --nome "$ORGANIZACAO_NOME" \
  --email "$ORGANIZACAO_EMAIL" \
  --telefone "$ORGANIZACAO_TELEFONE"

# Criar usuário
echo ""
echo "2️⃣  Criando usuário principal..."
python manage.py criar_usuario_principal \
  --username "$USUARIO_USERNAME" \
  --password "$USUARIO_PASSWORD" \
  --email "$USUARIO_EMAIL"

# Associar usuário ao organizador
echo ""
echo "3️⃣  Associando usuário ao organizador..."
python manage.py criar_organizador \
  --nome "$ORGANIZACAO_NOME" \
  --email "$ORGANIZACAO_EMAIL" \
  --usuario "$USUARIO_USERNAME"

echo ""
echo "✅ Organização criada com sucesso!"
echo ""
echo "📝 Credenciais de acesso:"
echo "   URL: https://seu-dominio.com/login/operacional/"
echo "   Username: $USUARIO_USERNAME"
echo "   Senha: $USUARIO_PASSWORD"
echo ""
echo "⚠️  Guarde estas credenciais com segurança!"

