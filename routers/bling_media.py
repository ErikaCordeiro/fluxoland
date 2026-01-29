from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, Response, StreamingResponse

router = APIRouter(
    prefix="/integracoes/bling/media",
    tags=["Bling Media"],
)

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(os.getenv("BLING_IMAGE_CACHE_DIR", str(Path("static") / "bling_cache")))
_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
_MAX_CACHE_BYTES = int(os.getenv("BLING_IMAGE_CACHE_MAX_BYTES", str(250 * 1024 * 1024)))  # 250MB


def _ensure_cache_dir() -> bool:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.warning("Cache de imagem indisponível (sem permissão/FS read-only): %s", e)
        return False


def _enforce_cache_limit() -> None:
    """Aplica um limite simples no cache (remove arquivos mais antigos).

    Best-effort: se falhar, não quebra a request.
    """
    try:
        if not _CACHE_DIR.exists():
            return
        files = [p for p in _CACHE_DIR.glob("*.*") if p.is_file() and not p.name.startswith(".")]
        if not files:
            return

        total = 0
        entries = []
        for p in files:
            st = p.stat()
            total += st.st_size
            entries.append((st.st_mtime, st.st_size, p))

        if total <= _MAX_CACHE_BYTES:
            return

        # remove os mais antigos primeiro
        entries.sort(key=lambda t: t[0])
        for _mtime, size, p in entries:
            try:
                p.unlink(missing_ok=True)
                total -= size
                if total <= _MAX_CACHE_BYTES:
                    break
            except Exception:
                continue
    except Exception:
        return


_FALLBACK_SVG = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"64\" height=\"64\" viewBox=\"0 0 64 64\">
    <rect width=\"64\" height=\"64\" rx=\"10\" fill=\"#f3f4f6\"/>
    <path d=\"M18 42h28V22H18v20zm2-2V24h24v16H20z\" fill=\"#9ca3af\"/>
    <path d=\"M22 36l6-6 5 5 5-6 4 7H22z\" fill=\"#9ca3af\"/>
    <text x=\"32\" y=\"54\" text-anchor=\"middle\" font-family=\"Arial, Helvetica, sans-serif\" font-size=\"10\" fill=\"#6b7280\">IMG</text>
</svg>"""


def _safe_ext_from_content_type(content_type: str | None) -> str:
    ct = (content_type or "").split(";", 1)[0].strip().lower()
    return {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/avif": ".avif",
    }.get(ct, "")


def _canonicalize_for_cache(url: str) -> str:
    """Gera uma versão canônica da URL para chave de cache.

    Para URLs assinadas (S3), remove parâmetros voláteis (x-amz-*, AWSAccessKeyId, Expires, Signature etc.).
    """
    p = urlparse(url)
    query = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        kl = (k or "").lower()
        if kl.startswith("x-amz-"):
            continue
        if kl in {"awsaccesskeyid", "expires", "signature", "securitytoken", "x-amz-signature"}:
            continue
        query.append((k, v))
    query_str = urlencode(query)
    return urlunparse((p.scheme, p.netloc, p.path, "", query_str, ""))


def _cache_key(url: str) -> str:
    canonical = _canonicalize_for_cache(url)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def _find_cached_file(key: str) -> Path | None:
    if not _CACHE_DIR.exists():
        return None
    matches = list(_CACHE_DIR.glob(f"{key}.*"))
    return matches[0] if matches else None


def _is_allowed_bling_host(host: str) -> bool:
    h = (host or "").lower()
    # evita SSRF: só permite domínios do Bling
    if h.endswith("bling.com.br") or h == "www.bling.com.br":
        return True

    # Algumas imagens do Bling vêm assinadas via S3 (ex.: orgbling.s3.amazonaws.com)
    # Mantém allowlist restrita: apenas hosts da AWS S3 que contenham 'bling'
    if h.endswith("amazonaws.com") and ".s3" in h and "bling" in h:
        return True

    return False


@router.get("/")
@router.get("")
def proxy_bling_image(
    url: str = Query(..., min_length=5),
):
    cache_ok = _ensure_cache_dir()

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="URL inválida")

    if not parsed.netloc or not _is_allowed_bling_host(parsed.netloc):
        raise HTTPException(status_code=400, detail="Host não permitido")

    key = _cache_key(url)
    if cache_ok:
        cached = _find_cached_file(key)
        if cached is not None:
            return RedirectResponse(url=f"/static/bling_cache/{cached.name}", status_code=302)

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    accept = "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"

    # Estratégia: alguns hosts do S3 do Bling negam hotlink. Tentamos variações de headers.
    header_candidates: list[dict[str, str]] = [
        {
            "User-Agent": user_agent,
            "Accept": accept,
            "Referer": "https://www.bling.com.br/doc.view.php",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        {
            "User-Agent": user_agent,
            "Accept": accept,
            "Referer": "https://www.bling.com.br/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        {
            "User-Agent": user_agent,
            "Accept": accept,
        },
        {},
    ]

    resp: requests.Response | None = None
    last_error: Exception | None = None

    for headers in header_candidates:
        try:
            resp = requests.get(url, headers=headers, timeout=25, stream=True, allow_redirects=True)
            if resp.status_code == 200:
                break
            # fecha antes de tentar de novo
            resp.close()
        except Exception as e:
            last_error = e
            resp = None

    if not resp or resp.status_code != 200:
        if last_error:
            logger.warning("Falha ao buscar imagem upstream (%s): %s", type(last_error).__name__, last_error)
        else:
            logger.warning("Imagem upstream retornou status=%s url=%s", getattr(resp, "status_code", None), url)
        return Response(content=_FALLBACK_SVG, media_type="image/svg+xml", headers={"Cache-Control": "private, max-age=300"})

    content_type = resp.headers.get("Content-Type")

    # Salva em cache local (static/bling_cache)
    ext = _safe_ext_from_content_type(content_type)
    if not ext:
        guess, _ = mimetypes.guess_type(parsed.path)
        ext = mimetypes.guess_extension(guess or "") or ".img"

    out_path = _CACHE_DIR / f"{key}{ext}"
    tmp_path = _CACHE_DIR / f".{key}{ext}.tmp"

    try:
        if not cache_ok:
            raise PermissionError("cache_desabilitado")

        total = 0
        with tmp_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > _MAX_IMAGE_BYTES:
                    raise ValueError("Imagem excede limite de tamanho")
                f.write(chunk)

        tmp_path.replace(out_path)
        _enforce_cache_limit()
        return RedirectResponse(url=f"/static/bling_cache/{out_path.name}", status_code=302)
    except Exception as e:
        logger.warning("Falha ao salvar cache local (%s): %s", type(e).__name__, e)
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass

        # fallback: stream sem cache (ou SVG se Content-Type suspeito)
        if not content_type or (content_type or "").startswith("text/"):
            return Response(content=_FALLBACK_SVG, media_type="image/svg+xml", headers={"Cache-Control": "private, max-age=300"})

        def _iter_stream():
            try:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        yield chunk
            finally:
                resp.close()

        return StreamingResponse(
            _iter_stream(),
            media_type=content_type,
            headers={"Cache-Control": "private, max-age=600"},
        )
