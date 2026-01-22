"""
Adiciona coluna 'desconto' na tabela 'propostas'
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import engine
from sqlalchemy import text

def run_migration():
    sql = """
    ALTER TABLE propostas ADD COLUMN IF NOT EXISTS desconto FLOAT;
    """
    
    with engine.connect() as conn:
        print("Executando migração: add_desconto_propostas")
        conn.execute(text(sql))
        conn.commit()
        print("✅ Coluna 'desconto' adicionada com sucesso à tabela 'propostas'")

if __name__ == "__main__":
    run_migration()
