import os
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User
from services.bling_import_service import BlingImportService
from integrations.bling.bling_services import (
    buscar_cliente_completo_por_pedido_numero,
    buscar_pedido_venda_completo,
    buscar_pedido_venda_por_id,
    mapear_pedido_para_importacao,
)


router = APIRouter(
    prefix="/integracoes/bling/webhook",
    tags=["Bling Webhook"],
)


@router.post("/")
async def receber_webhook_bling(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await _ler_payload(request)

    if not payload:
        return JSONResponse(
            {"erro": "Payload vazio ou invalido"},
            status_code=400,
        )

    if not _validar_webhook(request):
        return JSONResponse(
            {"erro": "Webhook nao autorizado"},
            status_code=401,
        )

    pedido_id, numero = _extrair_referencia(payload)

    pedido_payload = None
    if pedido_id:
        pedido_payload = buscar_pedido_venda_por_id(pedido_id)
    if not pedido_payload and numero:
        pedido_payload = buscar_pedido_venda_completo(numero)

    dados_importacao = mapear_pedido_para_importacao(pedido_payload)
    if not dados_importacao:
        return JSONResponse(
            {"erro": "Pedido nao encontrado no Bling"},
            status_code=404,
        )

    cliente_api = None
    if numero:
        try:
            cliente_api = buscar_cliente_completo_por_pedido_numero(numero)
        except Exception:
            cliente_api = None

    cliente_final = _merge_cliente(
        dados_importacao.get("cliente") or {},
        cliente_api,
    )

    vendedor_id = _get_default_user_id(db)
    if not vendedor_id:
        return JSONResponse(
            {"erro": "Nenhum usuario disponivel para importacao"},
            status_code=500,
        )

    id_bling = dados_importacao.get("id_bling") or pedido_id or numero

    BlingImportService.importar_proposta_bling(
        db=db,
        id_bling=str(id_bling),
        cliente=cliente_final or {"nome": "Cliente Bling"},
        itens=dados_importacao.get("itens") or [],
        vendedor_id=vendedor_id,
        observacao="Importado automaticamente via webhook Bling",
        pedido=dados_importacao.get("pedido"),
    )

    return {"status": "ok"}


def _validar_webhook(request: Request) -> bool:
    esperado = os.getenv("BLING_WEBHOOK_TOKEN")
    if not esperado:
        return True

    token = (
        request.headers.get("X-Bling-Token")
        or request.headers.get("X-Webhook-Token")
        or request.headers.get("Authorization")
    )
    if token and token.lower().startswith("bearer "):
        token = token[7:]

    return token == esperado


async def _ler_payload(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    try:
        form = await request.form()
        return dict(form)
    except Exception:
        return {}


def _extrair_referencia(payload: dict) -> tuple[str | None, str | None]:
    pedido_id = (
        payload.get("id")
        or payload.get("pedido_id")
        or payload.get("idPedido")
        or payload.get("id_pedido")
    )

    numero = (
        payload.get("numero")
        or payload.get("numero_loja")
        or payload.get("numeroLoja")
        or payload.get("numeroPedido")
    )

    pedido = payload.get("pedido") or payload.get("data")
    if isinstance(pedido, dict):
        pedido_id = pedido_id or pedido.get("id") or pedido.get("idPedido")
        numero = numero or pedido.get("numero") or pedido.get("numeroLoja")

    return (
        str(pedido_id) if pedido_id else None,
        str(numero) if numero else None,
    )


def _merge_cliente(base: dict, extra: dict | None) -> dict:
    if not extra:
        return base

    merged = dict(base)
    for key, value in extra.items():
        if not value:
            continue
        if not merged.get(key):
            merged[key] = value
    return merged


def _get_default_user_id(db: Session) -> int | None:
    user = (
        db.query(User)
        .filter(User.role == "lider")
        .order_by(User.id.asc())
        .first()
    )
    if not user:
        user = db.query(User).order_by(User.id.asc()).first()
    return user.id if user else None
