from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from auth import get_password_hash
from models import User
from templates import templates

router = APIRouter(prefix="/setup", tags=["Setup"])


@router.get("/create-admin", response_class=HTMLResponse)
def form_create_admin(request: Request):
    """Formulário para criar primeiro usuário admin"""
    return templates.TemplateResponse(
        "setup_admin.html",
        {"request": request}
    )


@router.post("/create-admin")
def create_admin(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    """Criar primeiro usuário admin - REMOVER APÓS USO"""
    
    # Verificar se já existe usuário
    existing_user = db.query(User).first()
    if existing_user:
        return templates.TemplateResponse(
            "setup_admin.html",
            {"request": request, "error": "Já existe um usuário cadastrado!"}
        )
    
    # Criar usuário admin
    user = User(
        nome=nome,
        email=email,
        senha_hash=get_password_hash(senha),
        role="lider"
    )
    db.add(user)
    db.commit()
    
    return RedirectResponse("/login?setup=success", status_code=HTTP_303_SEE_OTHER)
