from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from dependencies import get_current_user_html, require_lider_html
from templates import templates
from models import Transportadora

router = APIRouter(prefix="/transportadoras", tags=["transportadoras"])


# ======================================================
# LISTAGEM
# ======================================================
@router.get("/")
def listar_transportadoras(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    transportadoras = (
        db.query(Transportadora)
        .order_by(Transportadora.nome)
        .all()
    )

    return templates.TemplateResponse(
        "transportadoras_list.html",
        {
            "request": request,
            "user": user,
            "transportadoras": transportadoras,
        },
    )


# ======================================================
# CRIAR (SUBMIT DO MODAL / FORM)
# ======================================================
@router.post("/nova")
def criar_transportadora(
    nome: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    nome = nome.strip()

    if nome:
        existente = (
            db.query(Transportadora)
            .filter(Transportadora.nome == nome)
            .first()
        )

        if not existente:
            db.add(Transportadora(nome=nome))
            db.commit()

    return RedirectResponse(
        "/transportadoras",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# EXCLUIR
# ======================================================
@router.post("/{t_id}/excluir")
def excluir_transportadora(
    t_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    transportadora = db.get(Transportadora, t_id)

    if transportadora:
        try:
            db.delete(transportadora)
            db.commit()
        except Exception as e:
            db.rollback()
            # Se houver erro (ex: cotações usando esta transportadora),
            # apenas redireciona sem fazer nada
            pass

    return RedirectResponse(
        "/transportadoras",
        status_code=HTTP_303_SEE_OTHER,
    )
