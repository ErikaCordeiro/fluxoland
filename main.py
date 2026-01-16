import os
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from auth import router as auth_router
from routers import propostas, transportadoras, bling_import, caixas, simulacoes
from database import Base, engine, SessionLocal
from templates import templates
import models

# ----------------------------------
# ENV
# ----------------------------------
load_dotenv()

# ----------------------------------
# APP
# ----------------------------------
app = FastAPI(title="FluxoLand")

# ----------------------------------
# BANCO
# ----------------------------------
Base.metadata.create_all(bind=engine)

# Criar usuário admin padrão se não existir nenhum
from models import User
from auth import get_password_hash
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
        print("✅ Usuário admin padrão criado: sac@amferramentas.com.br / AmF123")
except Exception as e:
    print(f"⚠️ Erro ao criar usuário admin: {e}")
    db.rollback()
finally:
    db.close()

# ----------------------------------
# SESSÃO
# ----------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "dev-secret-key"),
)

# ----------------------------------
# STATIC E TEMPLATES
# ----------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
from templates import templates

# ----------------------------------
# ROTA HOME (CORRIGIDA)
# ----------------------------------
@app.get("/")
def home(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/propostas")
    return RedirectResponse("/login")

# ----------------------------------
# ROUTERS
# ----------------------------------
app.include_router(auth_router)             # /login /logout
app.include_router(propostas.router)        # /propostas
app.include_router(transportadoras.router)  # /transportadoras
app.include_router(bling_import.router)     # /integracoes/bling/importar
app.include_router(caixas.router)           # /caixas
app.include_router(simulacoes.router)       # /simulacoes

# ----------------------------------
# RUN LOCAL
# ----------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
