#!/usr/bin/env bash
set -euo pipefail

# Setup idempotente do PostgreSQL local para o Shiai (judocomp).
# Objetivo: resolver "FATAL: role \"vinicius\" does not exist" e criar o DB "shiai_db".
#
# Requisitos:
# - PostgreSQL rodando localmente
# - Acesso a sudo para executar comandos como o usuário "postgres"
#
# Uso:
#   bash scripts/setup_local_postgres.sh
#
# Depois:
#   export DB_NAME=shiai_db
#   export DB_USER=vinicius
#   python3 manage.py migrate
#   python3 manage.py runserver 0.0.0.0:8001

ROLE_NAME="${ROLE_NAME:-vinicius}"
DB_NAME="${DB_NAME:-shiai_db}"

psql_as_postgres() {
  # Evita warning "could not change directory" (postgres não tem permissão no CWD do usuário)
  # e garante execução não-interativa do psql.
  # Importante: passar argumentos com segurança (sem quebrar aspas).
  sudo -u postgres -H bash -lc 'cd / && psql -X -v ON_ERROR_STOP=1 "$@"' -- "$@"
}

echo "==> Checando psql e serviço local..."
command -v psql >/dev/null 2>&1 || { echo "ERRO: psql não encontrado. Instale postgresql-client."; exit 1; }
command -v pg_isready >/dev/null 2>&1 || { echo "ERRO: pg_isready não encontrado. Instale postgresql-client."; exit 1; }

pg_isready >/dev/null 2>&1 || {
  echo "ERRO: PostgreSQL não está pronto em /var/run/postgresql:5432."
  echo "Dica: sudo systemctl start postgresql"
  exit 1
}

echo "==> Criando role \"$ROLE_NAME\" (se não existir)..."
ROLE_EXISTS="$(psql_as_postgres -tAc "SELECT 1 FROM pg_catalog.pg_roles WHERE rolname='${ROLE_NAME}'")"
if [[ "${ROLE_EXISTS}" != "1" ]]; then
  psql_as_postgres -c "CREATE ROLE ${ROLE_NAME} LOGIN CREATEDB;"
else
  echo "   (role já existe)"
fi

echo "==> Criando database \"$DB_NAME\" (se não existir), owner=\"$ROLE_NAME\"..."
DB_EXISTS="$(psql_as_postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")"
if [[ "${DB_EXISTS}" != "1" ]]; then
  sudo -u postgres -H createdb -O "${ROLE_NAME}" "${DB_NAME}"
else
  echo "   (database já existe)"
fi

echo ""
echo "OK ✅"
echo "Próximos comandos:"
echo "  export DB_NAME=${DB_NAME}"
echo "  export DB_USER=${ROLE_NAME}"
echo "  python3 manage.py migrate"
echo "  python3 manage.py runserver 0.0.0.0:8001"


