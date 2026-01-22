from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy.orm import Session, joinedload

from database import get_db
from dependencies import get_current_user_html
from templates import templates
from models import Simulacao, Proposta

router = APIRouter(
    prefix="/simulacoes",
    tags=["Simulacoes"],
)


@router.get("/", response_class=HTMLResponse)
def listar_simulacoes(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    """Lista todas as simulações salvas no sistema"""
    
    simulacoes = (
        db.query(Simulacao)
        .join(Simulacao.proposta)
        .order_by(Simulacao.criado_em.desc())
        .all()
    )
    
    return templates.TemplateResponse(
        "simulacoes_list.html",
        {
            "request": request,
            "simulacoes": simulacoes,
            "user": user,
        },
    )


@router.post("/{simulacao_id}/editar")
def editar_simulacao(
    simulacao_id: int,
    descricao: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    """Edita a descrição de uma simulação"""
    
    simulacao = db.query(Simulacao).filter(Simulacao.id == simulacao_id).first()
    
    if simulacao:
        simulacao.descricao = descricao
        db.commit()
    
    return RedirectResponse("/simulacoes", status_code=HTTP_303_SEE_OTHER)


@router.post("/{simulacao_id}/deletar")
def deletar_simulacao(
    simulacao_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    """Deleta uma simulação"""
    
    simulacao = db.query(Simulacao).filter(Simulacao.id == simulacao_id).first()
    
    if simulacao:
        db.delete(simulacao)
        db.commit()
    
    return RedirectResponse("/simulacoes", status_code=HTTP_303_SEE_OTHER)
