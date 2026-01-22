"""
Migration: Adiciona coluna atualizado_em à tabela propostas
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from database import SessionLocal, engine
from sqlalchemy import text


def run_migration():
    """
    Adiciona coluna atualizado_em (TIMESTAMP) na tabela propostas
    e inicializa com o valor de criado_em
    """
    db = SessionLocal()
    try:
        print("🔄 Adicionando coluna 'atualizado_em' à tabela 'propostas'...")
        
        # 1. Adiciona a coluna (se não existir)
        db.execute(text("""
            ALTER TABLE propostas 
            ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP;
        """))
        
        # 2. Inicializa com criado_em para propostas existentes
        db.execute(text("""
            UPDATE propostas 
            SET atualizado_em = criado_em 
            WHERE atualizado_em IS NULL;
        """))
        
        db.commit()
        print("✅ Coluna 'atualizado_em' adicionada com sucesso à tabela 'propostas'")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao adicionar coluna: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
