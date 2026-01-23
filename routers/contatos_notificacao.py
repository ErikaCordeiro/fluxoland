from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db
from dependencies import get_current_user_html, require_lider_html
from templates import templates
from models import ContatoNotificacao, TipoNotificacao

router = APIRouter(prefix="/contatos-notificacao", tags=["contatos-notificacao"])


# ======================================================
# LISTAGEM
# ======================================================
@router.get("/")
def listar_contatos(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    contatos = (
        db.query(ContatoNotificacao)
        .order_by(ContatoNotificacao.tipo, ContatoNotificacao.nome)
        .all()
    )

    return templates.TemplateResponse(
        "contatos_notificacao_list.html",
        {
            "request": request,
            "user": user,
            "contatos": contatos,
        },
    )


# ======================================================
# CRIAR
# ======================================================
@router.post("/novo")
def criar_contato(
    nome: str = Form(...),
    telefone: str = Form(...),
    tipo: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    nome = nome.strip()
    telefone = telefone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    if nome and telefone:
        contato = ContatoNotificacao(
            nome=nome,
            telefone=telefone,
            tipo=TipoNotificacao(tipo),
            ativo=True,
        )
        db.add(contato)
        db.commit()

    return RedirectResponse(
        "/contatos-notificacao",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# EDITAR
# ======================================================
@router.post("/{contato_id}/editar")
def editar_contato(
    contato_id: int,
    nome: str = Form(...),
    telefone: str = Form(...),
    tipo: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    contato = db.get(ContatoNotificacao, contato_id)

    if contato:
        contato.nome = nome.strip()
        contato.telefone = telefone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        contato.tipo = TipoNotificacao(tipo)
        db.commit()

    return RedirectResponse(
        "/contatos-notificacao",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# EXCLUIR
# ======================================================
@router.post("/{contato_id}/excluir")
def excluir_contato(
    contato_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_lider_html),
):
    if isinstance(user, RedirectResponse):
        return user

    contato = db.get(ContatoNotificacao, contato_id)

    if contato:
        db.delete(contato)
        db.commit()

    return RedirectResponse(
        "/contatos-notificacao",
        status_code=HTTP_303_SEE_OTHER,
    )
