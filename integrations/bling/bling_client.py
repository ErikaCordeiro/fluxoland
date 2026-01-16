import requests
from typing import Optional

BASE_URL = "https://www.bling.com.br/Api/v3"

bling_token: Optional[dict] = None


def set_bling_token(token_data: dict):
    global bling_token
    bling_token = token_data


def get_headers() -> dict:
    if not bling_token:
        raise Exception("Token do Bling não configurado")

    return {
        "Authorization": f"Bearer {bling_token['access_token']}",
        "Accept": "application/json",
    }


def bling_get(endpoint: str, params: dict | None = None):
    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=get_headers(),
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()
