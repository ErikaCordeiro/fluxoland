from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from dependencies import get_current_user_html, require_lider_html
from templates import templates
from models import Caixa

router = APIRouter(prefix="/caixas", tags=["caixas"])


# ======================================================
# LISTAGEM
# ======================================================
@router.get("/")
def listar_caixas(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    caixas = (
        db.query(Caixa)
        .order_by(Caixa.nome)
        .all()
    )

    return templates.TemplateResponse(
        "caixas_list.html",
        {
            "request": request,
            "user": user,
            "caixas": caixas,
        },
    )


# ======================================================
# FORM NOVA CAIXA
# ======================================================
@router.get("/nova")
def nova_caixa(
    request: Request,
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "caixas_nova.html",
        {
            "request": request,
            "user": user,
        },
    )


# ======================================================
# CRIAR CAIXA
# ======================================================
@router.post("/nova")
def criar_caixa(
    nome: str = Form(...),
    altura_cm: float = Form(...),
    largura_cm: float = Form(...),
    comprimento_cm: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    nome = nome.strip()

    # validação mínima
    if not nome:
        return RedirectResponse(
            "/caixas",
            status_code=HTTP_303_SEE_OTHER,
        )

    caixa = Caixa(
        nome=nome,
        altura_cm=altura_cm,
        largura_cm=largura_cm,
        comprimento_cm=comprimento_cm,
    )

    db.add(caixa)
    db.commit()

    return RedirectResponse(
        "/caixas",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# EXCLUIR CAIXA
# ======================================================
@router.post("/{caixa_id}/excluir")
def excluir_caixa(
    caixa_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    caixa = db.get(Caixa, caixa_id)

    if caixa:
        db.delete(caixa)
        db.commit()

    return RedirectResponse(
        "/caixas",
        status_code=HTTP_303_SEE_OTHER,
    )
