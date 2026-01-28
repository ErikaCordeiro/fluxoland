import re


def parse_float_ptbr(value: str) -> float | None:
    """Converte número pt-BR para float.

    Exemplos:
    - "1,20" -> 1.2
    - "  150 " -> 150.0
    """

    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    try:
        return float(s.replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def _dim_to_cm(value: float) -> float:
    # Heurística: valores pequenos (<= 10) normalmente são metros (ex: 1,20m)
    # e valores maiores são centímetros (ex: 95cm, 120cm).
    return value * 100.0 if value <= 10 else value


def extrair_volume_total_cm3(descricao: str) -> float:
    """Extrai e soma volumes (cm³) a partir de um texto.

    Suporta padrões como:
    - "95x95x120"
    - "95 x 95 x 1,20"  (interpreta 1,20 como 1,20m => 120cm)
    - "4x95x95x1,20"    (quantidade antes das dimensões)
    - "(4x)95x95x1,20"  (quantidade entre parênteses)

    Retorna 0.0 quando não encontra dimensões.
    """

    texto = (descricao or "").strip()
    if not texto:
        return 0.0

    texto = re.sub(
        r"\(\s*(\d+)\s*[x×]\s*\)\s*",
        r"\1x",
        texto,
        flags=re.IGNORECASE,
    )

    volume_total_cm3 = 0.0

    dim_pattern = re.compile(
        r"(?:(\d+)\s*[x×]\s*)?(\d+(?:[\.,]\d+)?)\s*[x×]\s*(\d+(?:[\.,]\d+)?)\s*[x×]\s*(\d+(?:[\.,]\d+)?)",
        re.IGNORECASE,
    )

    for match in dim_pattern.finditer(texto):
        quantidade_str = match.group(1) or "1"
        d1 = parse_float_ptbr(match.group(2))
        d2 = parse_float_ptbr(match.group(3))
        d3 = parse_float_ptbr(match.group(4))

        if d1 is None or d2 is None or d3 is None:
            continue

        try:
            quantidade = int(quantidade_str)
        except ValueError:
            continue

        if quantidade <= 0:
            continue

        c = _dim_to_cm(d1)
        l = _dim_to_cm(d2)
        h = _dim_to_cm(d3)

        volume_total_cm3 += (c * l * h) * quantidade

    return volume_total_cm3


def extrair_peso_total_kg(descricao: str) -> float | None:
    """Extrai peso total (kg) a partir de um texto.

    Prioriza padrões explícitos:
    - "=peso 52,18" / "peso=52,18" / "peso: 52,18"

    Fallback: soma todos os pesos no formato "xxkg" encontrados no texto.

    Retorna None quando não encontra peso.
    """

    texto = (descricao or "").strip()
    if not texto:
        return None

    m = re.search(
        r"(?:=\s*peso|\bpeso\s*[:=])\s*(\d+(?:[\.,]\d+)?)\s*(?:kg)?",
        texto,
        re.IGNORECASE,
    )
    if m:
        v = parse_float_ptbr(m.group(1))
        return v if v is not None else None

    # Soma todos os pesos explícitos "xxkg"
    re_kg = re.compile(r"(\d+(?:[\.,]\d+)?)\s*kg\b", re.IGNORECASE)
    soma = 0.0
    encontrados = 0
    for m2 in re_kg.finditer(texto):
        v = parse_float_ptbr(m2.group(1))
        if v is None:
            continue
        soma += v
        encontrados += 1

    if encontrados > 0:
        return soma

    return None
