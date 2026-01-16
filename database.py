# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# ----------------------------------
# ENV
# ----------------------------------
load_dotenv(override=True)

# ----------------------------------
# DATABASE (SQLite local)
# ----------------------------------
DATABASE_URL = "sqlite:///./fluxoland.db"

# ----------------------------------
# ENGINE
# ----------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=True,  # deixe True enquanto estiver desenvolvendo
    connect_args={"check_same_thread": False},  # obrigatório no SQLite
)

# ----------------------------------
# SESSION
# ----------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ----------------------------------
# BASE (ÚNICA DO PROJETO)
# ----------------------------------
Base = declarative_base()

# ----------------------------------
# DEPENDENCY (FastAPI)
# ----------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
