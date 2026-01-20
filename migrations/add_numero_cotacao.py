"""
Migração: Adicionar coluna numero_cotacao na tabela cotacoes_frete

Execute este script uma vez para atualizar o banco de dados:
python migrations/add_numero_cotacao.py
"""

import os
import sys
from sqlalchemy import create_engine, text

# Adiciona o diretório raiz ao path para importar database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_URL

def run_migration():
    print("🔄 Iniciando migração: add_numero_cotacao")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verifica se a coluna já existe
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cotacoes_frete' 
            AND column_name = 'numero_cotacao'
        """))
        
        if result.fetchone():
            print("✅ Coluna 'numero_cotacao' já existe. Nenhuma ação necessária.")
            return
        
        # Adiciona a coluna
        print("📝 Adicionando coluna 'numero_cotacao' na tabela 'cotacoes_frete'...")
        conn.execute(text("ALTER TABLE cotacoes_frete ADD COLUMN numero_cotacao VARCHAR"))
        conn.commit()
        
        print("✅ Migração concluída com sucesso!")
        print("   - Coluna 'numero_cotacao' adicionada")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)
