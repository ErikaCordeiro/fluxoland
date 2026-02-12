import json
import logging
import os
import requests
from typing import Optional

from database import SessionLocal
from models import BlingToken

BASE_URL = "https://www.bling.com.br/Api/v3"

TOKEN_PATH = os.getenv("BLING_TOKEN_PATH", ".bling_token.json")
bling_token: Optional[dict] = None
logger = logging.getLogger(__name__)


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


def _load_token_from_db() -> Optional[dict]:
    db = SessionLocal()
    try:
        registro = db.query(BlingToken).order_by(BlingToken.atualizado_em.desc()).first()
        if not registro or not registro.token_json:
            return None
        data = json.loads(registro.token_json)
        if isinstance(data, dict) and data.get("access_token"):
            return data
    except Exception as exc:
        logger.info("[BLING] falha ao carregar token do banco: %s", exc)
        return None
    finally:
        db.close()
    return None


def _save_token_to_disk(token_data: dict) -> None:
    try:
        with open(TOKEN_PATH, "w", encoding="utf-8") as handle:
            json.dump(token_data, handle)
    except Exception:
        return


def _save_token_to_db(token_data: dict) -> None:
    db = SessionLocal()
    try:
        token_json = json.dumps(token_data)
        registro = db.query(BlingToken).first()
        if not registro:
            registro = BlingToken(token_json=token_json)
            db.add(registro)
        else:
            registro.token_json = token_json
        db.commit()
    except Exception as exc:
        logger.info("[BLING] falha ao salvar token no banco: %s", exc)
        db.rollback()
    finally:
        db.close()


def set_bling_token(token_data: dict):
    global bling_token
    bling_token = token_data
    _save_token_to_disk(token_data)
    _save_token_to_db(token_data)


def _ensure_token_loaded() -> None:
    global bling_token
    if bling_token:
        return
    token_disk = _load_token_from_disk()
    if token_disk:
        bling_token = token_disk
        return
    token_db = _load_token_from_db()
    if token_db:
        bling_token = token_db


def get_headers() -> dict:
    _ensure_token_loaded()
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


bling_token = _load_token_from_disk() or _load_token_from_db()
