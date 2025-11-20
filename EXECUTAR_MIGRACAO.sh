#!/bin/bash
# Script para executar a migração completa do evento histórico

echo "🚀 Iniciando migração do evento histórico..."
echo ""

# Aplicar migrações do banco
echo "📦 Aplicando migrações do banco de dados..."
python3 manage.py migrate eventos --noinput

# Executar comando de migração (dry-run primeiro)
echo ""
echo "🔍 Executando DRY-RUN (simulação)..."
python3 manage.py migrar_evento_historico --dry-run

echo ""
echo "⚠️  Se o dry-run estiver OK, execute:"
echo "   python3 manage.py migrar_evento_historico"
echo ""
echo "✅ Migração concluída!"


