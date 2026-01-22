"""
Adiciona coluna 'automatica' na tabela 'simulacoes'
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import engine
from sqlalchemy import text

def run_migration():
    sql = """
    -- Adiciona a coluna 'automatica' à tabela simulacoes
    ALTER TABLE simulacoes ADD COLUMN automatica BOOLEAN DEFAULT FALSE;
    
    -- Atualiza simulacoes existentes como não automáticas (padrão)
    UPDATE simulacoes SET automatica = FALSE WHERE automatica IS NULL;
    """
    
    with engine.connect() as conn:
        print("Executando migração: add_simulacao_automatica")
        conn.execute(text(sql))
        conn.commit()
        print("✅ Coluna 'automatica' adicionada com sucesso à tabela 'simulacoes'")

if __name__ == "__main__":
    run_migration()
