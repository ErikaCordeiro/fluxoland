from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user_html
from templates import templates
from models import Proposta, PropostaStatus, Cliente, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _get_dashboard_stats(db: Session) -> Dict[str, Any]:
    today = datetime.now().date()
    
    # Propostas de hoje
    propostas_hoje = db.query(func.count(Proposta.id)).filter(
        func.date(Proposta.criado_em) == today
    ).scalar() or 0
    
    # Propostas por status
    em_simulacao = db.query(func.count(Proposta.id)).filter(
        Proposta.status == PropostaStatus.pendente_simulacao
    ).scalar() or 0
    
    em_cotacao = db.query(func.count(Proposta.id)).filter(
        Proposta.status == PropostaStatus.pendente_cotacao
    ).scalar() or 0
    
    em_envio = db.query(func.count(Proposta.id)).filter(
        Proposta.status == PropostaStatus.pendente_envio
    ).scalar() or 0
    
    # Valor total do dia - calculado manualmente pois valor_total é uma property
    propostas_dia = db.query(Proposta).filter(
        func.date(Proposta.criado_em) == today
    ).all()
    
    valor_dia = sum(proposta.valor_total for proposta in propostas_dia)
    
    return {
        "propostas_hoje": propostas_hoje,
        "em_simulacao": em_simulacao,
        "em_cotacao": em_cotacao,
        "em_envio": em_envio,
        "valor_dia": float(valor_dia) if valor_dia else 0,
    }


def _get_recent_activities(db: Session, limit: int = 5) -> list:
    propostas = (
        db.query(Proposta)
        .join(Cliente)
        .order_by(Proposta.criado_em.desc())
        .limit(limit)
        .all()
    )
    
    activities = []
    for proposta in propostas:
        # Calculate time difference
        now = datetime.now()
        diff = now - proposta.criado_em
        
        if diff.days > 0:
            tempo_relativo = f"{diff.days}d atrás"
        elif diff.seconds // 3600 > 0:
            tempo_relativo = f"{diff.seconds // 3600}h atrás"
        else:
            tempo_relativo = f"{diff.seconds // 60} min atrás"
        
        activities.append({
            "id": proposta.id,
            "numero": f"#{proposta.id}",
            "cliente": proposta.cliente.nome,
            "status": proposta.status.value,
            "valor": proposta.valor_total,
            "tempo_relativo": tempo_relativo,
        })
    
    return activities


def _get_chart_data_status(db: Session) -> Dict[str, int]:
    em_simulacao = db.query(func.count(Proposta.id)).filter(
        Proposta.status == PropostaStatus.pendente_simulacao
    ).scalar() or 0
    
    em_cotacao = db.query(func.count(Proposta.id)).filter(
        Proposta.status == PropostaStatus.pendente_cotacao
    ).scalar() or 0
    
    em_envio = db.query(func.count(Proposta.id)).filter(
        Proposta.status == PropostaStatus.pendente_envio
    ).scalar() or 0
    
    return {
        "simulacao": em_simulacao,
        "cotacao": em_cotacao,
        "envio": em_envio,
    }


def _get_chart_data_evolution(db: Session, days: int = 7) -> Dict[str, list]:
    today = datetime.now().date()
    dates = []
    counts = []
    
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        count = db.query(func.count(Proposta.id)).filter(
            func.date(Proposta.criado_em) == date
        ).scalar() or 0
        
        dates.append(date.strftime("%d/%m"))
        counts.append(count)
    
    return {
        "dates": dates,
        "counts": counts,
    }


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    """Main dashboard view.
    
    Args:
        request: FastAPI request object.
        db: Database session.
        user: Current authenticated user.
        
    Returns:
        Rendered dashboard template.
    """
    if isinstance(user, RedirectResponse):
        return user
    
    try:
        # Get all dashboard data
        stats = _get_dashboard_stats(db)
        activities = _get_recent_activities(db)
        chart_status = _get_chart_data_status(db)
        chart_evolution = _get_chart_data_evolution(db)
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "stats": stats,
                "activities": activities,
                "chart_status": chart_status,
                "chart_evolution": chart_evolution,
            },
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "error": "Erro ao carregar dashboard",
            },
            status_code=500,
        )
