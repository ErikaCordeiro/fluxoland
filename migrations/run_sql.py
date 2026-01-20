"""
Executa SQL direto no banco de produção
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL não encontrada!")
    exit(1)

print(f"🔗 Conectando ao banco: {DATABASE_URL[:30]}...")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("📝 Executando: ALTER TABLE cotacoes_frete ADD COLUMN numero_cotacao VARCHAR")
    
    try:
        conn.execute(text("ALTER TABLE cotacoes_frete ADD COLUMN numero_cotacao VARCHAR"))
        conn.commit()
        print("✅ Coluna adicionada com sucesso!")
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e):
            print("✅ Coluna já existe!")
        else:
            print(f"❌ Erro: {e}")
            raise
