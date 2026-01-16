# create_tables.py
from database import Base, engine
import models  # força carregar todos os models

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso.")

if __name__ == "__main__":
    create_tables()
