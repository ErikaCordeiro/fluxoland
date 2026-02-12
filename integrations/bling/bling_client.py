import json
import os
import requests
from typing import Optional

BASE_URL = "https://www.bling.com.br/Api/v3"

TOKEN_PATH = os.getenv("BLING_TOKEN_PATH", ".bling_token.json")
bling_token: Optional[dict] = None


def _load_token_from_disk() -> Optional[dict]:
    if not os.path.exists(TOKEN_PATH):
        return None
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and data.get("access_token"):
            return data
    except Exception:
        return None
    return None


def _save_token_to_disk(token_data: dict) -> None:
    try:
        with open(TOKEN_PATH, "w", encoding="utf-8") as handle:
            json.dump(token_data, handle)
    except Exception:
        return


def set_bling_token(token_data: dict):
    global bling_token
    bling_token = token_data
    _save_token_to_disk(token_data)


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


bling_token = _load_token_from_disk()
