"""FluxoLand - Sistema de Gestão de Propostas e Fretes.

FastAPI application for managing commercial proposals,
freight calculations, and Bling integration.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import text

from auth import get_password_hash, router as auth_router
from database import Base, SessionLocal, engine
from models import User
from routers import bling_import, caixas, propostas, simulacoes, transportadoras, contatos_notificacao, dashboard
from templates import templates
from auto_migrate import verificar_e_executar_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Evita logs verbosos do SQLAlchemy em produção.
# Se precisar depurar SQL, use `DEBUG=true` (e opcionalmente ajuste nível dos loggers).
for _logger_name in [
    "sqlalchemy.engine",
    "sqlalchemy.engine.Engine",
    "sqlalchemy.orm",
    "sqlalchemy.pool",
]:
    logging.getLogger(_logger_name).setLevel(logging.WARNING)

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting FluxoLand application...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Run auto-migrations (Dashboard + WhatsApp)
    verificar_e_executar_migrations()
    
    # Run legacy migrations
    _run_migrations()
    
    # Create default admin user if needed
    _create_default_admin()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FluxoLand application...")


def _run_migrations() -> None:
    """Run database migrations."""
    db = SessionLocal()
    try:
        logger.info("Running database migrations...")
        
        # Migration 1: Add desconto column to propostas
        try:
            db.execute(text(
                "ALTER TABLE propostas ADD COLUMN IF NOT EXISTS desconto FLOAT;"
            ))
            db.commit()
            logger.info("✓ Migration: desconto column added")
        except Exception as e:
            logger.error(f"Migration desconto failed: {e}")
            db.rollback()
        
        # Migration 2: Add atualizado_em column to propostas
        try:
            db.execute(text(
                "ALTER TABLE propostas ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP;"
            ))
            db.commit()
            logger.info("✓ Migration: atualizado_em column added")
        except Exception as e:
            logger.error(f"Migration atualizado_em failed: {e}")
            db.rollback()
        
        # Migration 3: Populate atualizado_em with criado_em
        try:
            db.execute(text(
                "UPDATE propostas SET atualizado_em = criado_em WHERE atualizado_em IS NULL;"
            ))
            db.commit()
            logger.info("✓ Migration: atualizado_em populated")
        except Exception as e:
            logger.error(f"Migration atualizado_em populate failed: {e}")
            db.rollback()
        
        # Migration 4: Add automatica column to simulacoes
        try:
            db.execute(text(
                "ALTER TABLE simulacoes ADD COLUMN IF NOT EXISTS automatica BOOLEAN DEFAULT FALSE;"
            ))
            db.commit()
            logger.info("✓ Migration: simulacoes.automatica column added")
        except Exception as e:
            logger.error(f"Migration simulacoes.automatica failed: {e}")
            db.rollback()
        
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        db.rollback()
    finally:
        db.close()


def _create_default_admin() -> None:
    """Create default admin user if no users exist."""
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin_user = User(
                nome="SAC AM Ferramentas",
                email="sac@amferramentas.com.br",
                senha_hash=get_password_hash("AmF123"),
                role="lider"
            )
            db.add(admin_user)
            db.commit()
            logger.info(
                "Default admin user created: sac@amferramentas.com.br / AmF123"
            )
    except Exception as e:
        logger.error(f"Error creating default admin user: {e}")
        db.rollback()
    finally:
        db.close()


# Create FastAPI application
app = FastAPI(
    title="FluxoLand",
    description="Sistema de Gestão de Propostas e Fretes",
    version="1.0.0",
    lifespan=lifespan,
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "dev-secret-key"),
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Favicon route
@app.get("/favicon.ico", tags=["static"])
async def favicon():
    """Serve the favicon."""
    return RedirectResponse(url="/static/favicon.ico", status_code=301)


# Root route
@app.get("/", tags=["navigation"])
async def home(request: Request) -> RedirectResponse:
    """Redirect to login or dashboard based on authentication status."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


# Include routers
app.include_router(auth_router, tags=["authentication"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(propostas.router, tags=["propostas"])
app.include_router(transportadoras.router, tags=["transportadoras"])
app.include_router(bling_import.router, tags=["integrations"])
app.include_router(caixas.router, tags=["caixas"])
app.include_router(simulacoes.router, tags=["simulacoes"])
app.include_router(contatos_notificacao.router, tags=["notificacoes"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
