"""Database configuration and session management.

Provides SQLAlchemy engine, session maker, and base model class.
Supports both PostgreSQL (production) and SQLite (development).
"""

import logging
import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to SQLite for development
if not DATABASE_URL or DATABASE_URL == "postgresql://postgres:postgres@localhost:5432/fluxoland":
    DATABASE_URL = "sqlite:///./fluxoland.db"
    logger.warning(
        "Using SQLite for development. "
        "Set DATABASE_URL in .env to use PostgreSQL."
    )

# Determine if debug mode is enabled
DEBUG = os.getenv("DEBUG", "true").lower() == "true"


def create_db_engine() -> Engine:
    """Create and configure the database engine.
    
    Returns:
        Configured SQLAlchemy engine instance.
    """
    is_sqlite = DATABASE_URL.startswith("sqlite")
    
    if is_sqlite:
        return create_engine(
            DATABASE_URL,
            echo=DEBUG,
            connect_args={"check_same_thread": False},
        )
    else:
        return create_engine(
            DATABASE_URL,
            echo=DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )


# Create engine and session maker
engine = create_db_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    
    Yields:
        Database session that is automatically closed after use.
    
    Example:
        ```python
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
