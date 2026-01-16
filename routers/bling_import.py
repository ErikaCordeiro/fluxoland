from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy.orm import Session
from urllib.parse import urlparse, parse_qs

from database import get_db
from dependencies import get_current_user_api
from services.bling_import_service import BlingImportService
from services.bling_parser_service import BlingParserService

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
    dados = BlingParserService.parse_doc_view(link_bling)

    BlingImportService.importar_proposta_bling(
        db=db,
        id_bling=dados.get("id_bling") or id_bling,
        cliente=dados.get("cliente", {"nome": "Cliente Bling"}),
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
