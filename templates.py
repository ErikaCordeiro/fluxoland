from fastapi.templating import Jinja2Templates
from urllib.parse import quote, urlparse, urljoin

from config import settings


templates = Jinja2Templates(directory="templates")

# Globais para templates
templates.env.globals["PESO_CUBADO_FATOR"] = settings.peso_cubado_fator


def format_money(value):
    try:
        v = float(value or 0)
    except Exception:
        return "R$ 0,00"
    # formata com separador de milhares ponto e decimal vírgula: 3.152,77
    s = f"{v:,.2f}"  # exemplo: '3,152.77'
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


templates.env.filters["money"] = format_money


def format_money_no_symbol(value):
    try:
        v = float(value or 0)
    except Exception:
        return "0,00"
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def format_percent(value):
    try:
        v = float(value or 0)
    except Exception:
        return "0,00%"
    s = f"{v:.2f}".replace('.', ',')
    return f"{s}%"


templates.env.filters["money_no_symbol"] = format_money_no_symbol
templates.env.filters["percent"] = format_percent


def bling_image_src(value):
    """Converte URL de imagem do Bling para endpoint de proxy.

    Evita bloqueio por hotlink/referer/CORS no browser.
    """
    if value is None:
        return ""
    url = str(value).strip()
    if not url:
        return ""

    # Normaliza paths relativos para o domínio do Bling
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if not parsed.scheme and not parsed.netloc:
        url = urljoin("https://www.bling.com.br/", url)
        parsed = urlparse(url)

    host = (parsed.netloc or "").lower()
    is_bling_host = host.endswith("bling.com.br") or host == "www.bling.com.br"
    is_bling_s3_host = host.endswith("amazonaws.com") and ".s3" in host and "bling" in host

    if parsed.scheme in {"http", "https"} and (is_bling_host or is_bling_s3_host):
        return f"/integracoes/bling/media?url={quote(url, safe='')}"

    return url


templates.env.filters["bling_image_src"] = bling_image_src
