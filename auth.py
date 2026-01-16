from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User

router = APIRouter()
from templates import templates

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ======================================================
# FUNÇÕES DE SENHA
# ======================================================

def get_password_hash(password: str) -> str:
    # Bcrypt tem limite de 72 bytes - truncar se necessário
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        # Aplicar mesmo truncamento na verificação
        plain_bytes = plain.encode('utf-8')[:72]
        return pwd_context.verify(plain_bytes.decode('utf-8', errors='ignore'), hashed)
    except Exception:
        return False


# ======================================================
# ROTAS
# ======================================================

@router.get("/login")
def get_login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
    )


@router.post("/login")
def post_login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
):
    db: Session = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        # validações
        if not user or not verify_password(senha, user.senha_hash):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "erro": "Usuário ou senha inválidos",
                },
                status_code=400,
            )

        if not user.ativo:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "erro": "Usuário inativo",
                },
                status_code=400,
            )

        # LOGIN OK → SALVA NA SESSÃO
        request.session["user_id"] = user.id
        request.session["user_nome"] = user.nome
        request.session["user_role"] = user.role.value

        return RedirectResponse(
            url="/propostas",
            status_code=HTTP_302_FOUND,
        )

    finally:
        db.close()


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="/login",
        status_code=HTTP_302_FOUND,
    )
