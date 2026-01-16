import os
import secrets
import requests
from urllib.parse import urlencode

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, JSONResponse

from integrations.bling.bling_client import set_bling_token

router = APIRouter(
    prefix="/integracoes/bling",
    tags=["Bling"]
)

BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"


def gerar_url_autorizacao() -> str:
    client_id = os.getenv("BLING_CLIENT_ID")
    redirect_uri = os.getenv("BLING_REDIRECT_URI")

    if not client_id or not redirect_uri:
        return ""

    state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    return f"{BLING_AUTH_URL}?{urlencode(params)}"


def trocar_code_por_token(code: str) -> dict:
    client_id = os.getenv("BLING_CLIENT_ID")
    client_secret = os.getenv("BLING_CLIENT_SECRET")
    redirect_uri = os.getenv("BLING_REDIRECT_URI")

    response = requests.post(
        BLING_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )

    response.raise_for_status()

    token_data = response.json()

    # salva token em memória (DEV)
    set_bling_token(token_data)

    return token_data


@router.get("/")
def iniciar_oauth():
    url = gerar_url_autorizacao()

    if not url:
        return JSONResponse(
            {"erro": "Variáveis do Bling não configuradas"},
            status_code=500,
        )

    return RedirectResponse(url)


@router.get("/callback")
def callback(code: str | None = None):
    if not code:
        return JSONResponse(
            {"erro": "Code não recebido do Bling"},
            status_code=400,
        )

    trocar_code_por_token(code)

    return {
        "status": "ok",
        "mensagem": "Bling conectado com sucesso",
    }
