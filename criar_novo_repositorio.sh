#!/bin/bash

# Script para criar um novo repositório no GitHub
# Requer: GitHub CLI (gh) instalado e autenticado

echo "🚀 Criando novo repositório no GitHub..."
echo ""

# Verificar se GitHub CLI está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) não está instalado."
    echo "📦 Instale com: sudo apt install gh"
    echo "🔐 Autentique com: gh auth login"
    exit 1
fi

# Verificar se está autenticado
if ! gh auth status &> /dev/null; then
    echo "❌ Não está autenticado no GitHub CLI."
    echo "🔐 Execute: gh auth login"
    exit 1
fi

# Solicitar informações do repositório
read -p "📝 Nome do novo repositório: " REPO_NAME
read -p "📄 Descrição (opcional): " REPO_DESC
read -p "🔒 Repositório privado? (s/N): " IS_PRIVATE

# Definir visibilidade
if [[ "$IS_PRIVATE" =~ ^[Ss]$ ]]; then
    VISIBILITY="--private"
else
    VISIBILITY="--public"
fi

# Criar repositório
echo ""
echo "⏳ Criando repositório '$REPO_NAME'..."
gh repo create "$REPO_NAME" $VISIBILITY --description "$REPO_DESC" --source=. --remote=new-origin --push

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Repositório criado com sucesso!"
    echo "🌐 URL: https://github.com/$(gh api user --jq .login)/$REPO_NAME"
    echo ""
    echo "📋 Remotes configurados:"
    git remote -v
else
    echo ""
    echo "❌ Erro ao criar repositório."
    exit 1
fi

