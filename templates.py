from fastapi.templating import Jinja2Templates

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
