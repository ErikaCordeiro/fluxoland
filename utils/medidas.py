from __future__ import annotations


def cm_para_m(valor_cm: float | int | None) -> float:
    """Converte centímetros para metros."""

    return float(valor_cm or 0) / 100


def format_dimensoes_m(
    comprimento_cm: float | int | None,
    largura_cm: float | int | None,
    altura_cm: float | int | None,
    *,
    casas: int = 2,
) -> str:
    """Formata dimensões em metros no padrão '0.95x0.98x1.20'."""

    c = cm_para_m(comprimento_cm)
    l = cm_para_m(largura_cm)
    a = cm_para_m(altura_cm)

    fmt = f"{{:.{casas}f}}"
    return f"{fmt.format(c)}x{fmt.format(l)}x{fmt.format(a)}"
