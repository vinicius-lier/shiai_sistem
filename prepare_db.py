#!/usr/bin/env python3
"""
Script para criar o arquivo do banco de dados ANTES de qualquer import do Django.
Este script deve ser executado antes de qualquer comando Django no Render.
"""
import os
import sys

def create_database_file():
    """Cria o arquivo do banco de dados se não existir"""
    if os.environ.get("RENDER"):
        db_path = "/var/data/db.sqlite3"
        db_dir = "/var/data"
        
        # Criar diretório se não existir
        os.makedirs(db_dir, exist_ok=True)
        os.chmod(db_dir, 0o755)
        
        # Criar arquivo do banco se não existir
        if not os.path.exists(db_path):
            with open(db_path, 'w') as f:
                f.write('')  # Criar arquivo vazio
            os.chmod(db_path, 0o644)
            print(f"✅ Arquivo do banco criado: {db_path}")
        else:
            # Garantir permissões corretas
            os.chmod(db_path, 0o644)
            print(f"✅ Arquivo do banco já existe: {db_path}")
        
        # Verificar se foi criado corretamente
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            print(f"   Permissões: {oct(stat.st_mode)}")
            print(f"   Tamanho: {stat.st_size} bytes")
            return True
        else:
            print(f"❌ ERRO: Não foi possível criar {db_path}")
            return False
    else:
        print("ℹ️  Ambiente local - não é necessário criar arquivo do banco")
        return True

if __name__ == "__main__":
    success = create_database_file()
    sys.exit(0 if success else 1)

