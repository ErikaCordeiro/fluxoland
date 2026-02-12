from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy.orm import Session
from urllib.parse import urlparse, parse_qs

from database import get_db
from dependencies import get_current_user_api
from services.bling_import_service import BlingImportService
from services.bling_parser_service import BlingParserService
from integrations.bling.bling_services import buscar_cliente_completo_por_pedido_numero

router = APIRouter(
    prefix="/integracoes/bling/importar",
    tags=["Bling Import"],
)


# ======================================================
# IMPORTAÇÃO VIA LINK doc.view.php
# ======================================================
@router.post("/")
def importar_proposta_por_link(
    link_bling: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_api),
):
    """
    Exemplo:
    https://www.bling.com.br/doc.view.php?id=HASH
    """

    id_bling = extrair_id_bling(link_bling)

    if not id_bling:
        return RedirectResponse(
            "/propostas?erro=link_invalido",
            status_code=HTTP_303_SEE_OTHER,
        )

    # tentar parsear o documento público do Bling e importar
    try:
        dados = BlingParserService.parse_doc_view(link_bling)
    except ValueError:
        return RedirectResponse(
            "/propostas?erro=bling_link_invalido",
            status_code=HTTP_303_SEE_OTHER,
        )

    # Normaliza dados mascarados do doc.view (ex: ***) para permitir enriquecimento via API
    cliente_doc_view = dados.get("cliente", {}) or {}
    cliente_doc_view = _limpar_dados_mascarados(cliente_doc_view)

    # Tenta enriquecer com dados completos via API autenticada do Bling
    pedido = dados.get("pedido") or {}
    numero_pedido = None
    if isinstance(pedido, dict):
        numero_pedido = pedido.get("numero")

    cliente_api = None
    if numero_pedido:
        try:
            cliente_api = buscar_cliente_completo_por_pedido_numero(numero_pedido)
        except Exception:
            cliente_api = None

    cliente_final = _merge_cliente(cliente_doc_view, cliente_api)

    BlingImportService.importar_proposta_bling(
        db=db,
        id_bling=dados.get("id_bling") or id_bling,
        cliente=cliente_final or {"nome": "Cliente Bling"},
        itens=dados.get("itens", []),
        vendedor_id=user.id,
        observacao="Importado via Bling",
        pedido=dados.get("pedido"),
    )

    return RedirectResponse(
        "/propostas",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# UTIL
# ======================================================
def extrair_id_bling(link: str) -> str | None:
    try:
        parsed = urlparse(link)
        query = parse_qs(parsed.query)

        if "id" not in query or not query["id"]:
            return None

        return query["id"][0]
    except Exception:
        return None


def _limpar_dados_mascarados(cliente: dict) -> dict:
    """Remove campos mascarados (***), deixando-os vazios para permitir enriquecimento."""

    def _clean(value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        v = value.strip()
        if not v:
            return None
        if "*" in v:
            return None
        return v

    return {
        "nome": _clean(cliente.get("nome")),
        "documento": _clean(cliente.get("documento")),
        "endereco": _clean(cliente.get("endereco")),
        "cidade": _clean(cliente.get("cidade")),
        "telefone": _clean(cliente.get("telefone")),
        "email": _clean(cliente.get("email")),
        "cep": _clean(cliente.get("cep")),
    }


def _merge_cliente(base: dict, extra: dict | None) -> dict:
    """Preenche campos vazios do base com dados do extra."""
    if not extra:
        return base

    merged = dict(base)
    for key, value in extra.items():
        if not value:
            continue
        if not merged.get(key):
            merged[key] = value
    return merged
