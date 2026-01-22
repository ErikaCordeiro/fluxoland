"""Executa migrações no banco de produção"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()

try:
    print("Executando migrações...")
    
    # Migração 1: adicionar desconto
    print("\n1. Adicionando coluna 'desconto'...")
    db.execute(text("ALTER TABLE propostas ADD COLUMN IF NOT EXISTS desconto FLOAT;"))
    db.commit()
    print("✅ Desconto adicionado!")
    
    # Migração 2: adicionar atualizado_em
    print("\n2. Adicionando coluna 'atualizado_em'...")
    db.execute(text("ALTER TABLE propostas ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP;"))
    db.commit()
    print("✅ atualizado_em adicionado!")
    
    # Migração 3: preencher atualizado_em com criado_em
    print("\n3. Preenchendo atualizado_em...")
    db.execute(text("UPDATE propostas SET atualizado_em = criado_em WHERE atualizado_em IS NULL;"))
    db.commit()
    print("✅ atualizado_em preenchido!")
    
    print("\n🎉 Todas as migrações executadas com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    db.rollback()
finally:
    db.close()
