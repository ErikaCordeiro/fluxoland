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
        s = s.replace(" ", "")
        # Remove separador de milhar pt-BR (ex: 1.358 -> 1358)
        s = re.sub(r"\.(?=\d{3}(?:\D|$))", "", s)
        s = s.replace(",", ".")
        return float(s)
    except ValueError:
        return None


def _dim_to_cm(raw: str, value: float, *, unit: str | None) -> float:
    """Converte dimensão para cm.

    Regras:
    - Se a unidade do match for 'cm': mantém como cm.
    - Se a unidade do match for 'm': converte tudo para cm.
    - Sem unidade: se o token tem decimal (1,20 / 1.20), assume metros; caso contrário assume cm.
    """

    if unit == "cm":
        return value
    if unit == "m":
        return value * 100.0

    # Sem unidade explícita: decimal costuma indicar metros (1,20m)
    if raw and ("," in raw or "." in raw):
        return value * 100.0

    return value


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

    # Normaliza quantidades entre parênteses:
    # - (4x)95x95x1,20  -> 4x95x95x1,20
    # - (28) 13x125x184 -> 28x13x125x184
    texto = re.sub(
        r"\(\s*(\d+)\s*(?:[x×])?\s*\)\s*",
        r"\1x",
        texto,
        flags=re.IGNORECASE,
    )

    volume_total_cm3 = 0.0
    volume_sem_qtd_cm3 = 0.0
    encontrou_com_qtd = False

    dim_pattern = re.compile(
        r"(?:(\d+)\s*[x×]\s*)?"  # quantidade opcional
        r"(\d+(?:[\.,]\d+)?)\s*[x×]\s*"
        r"(\d+(?:[\.,]\d+)?)\s*[x×]\s*"
        r"(\d+(?:[\.,]\d+)?)",
        re.IGNORECASE,
    )

    for match in dim_pattern.finditer(texto):
        quantidade_str = match.group(1) or "1"
        raw1 = match.group(2)
        raw2 = match.group(3)
        raw3 = match.group(4)
        d1 = parse_float_ptbr(raw1)
        d2 = parse_float_ptbr(raw2)
        d3 = parse_float_ptbr(raw3)

        if d1 is None or d2 is None or d3 is None:
            continue

        try:
            quantidade = int(quantidade_str)
        except ValueError:
            continue

        if quantidade <= 0:
            continue

        # Tenta detectar unidade logo após o match: "cm" ou "m"
        unit = None
        tail = texto[match.end() : match.end() + 10].lower()
        if re.search(r"\bcm\b", tail):
            unit = "cm"
        elif re.search(r"\bm\b", tail):
            unit = "m"

        c = _dim_to_cm(raw1, d1, unit=unit)
        l = _dim_to_cm(raw2, d2, unit=unit)
        h = _dim_to_cm(raw3, d3, unit=unit)

        vol_linha = (c * l * h) * quantidade
        # Heurística anti-duplicidade: se houver match com quantidade,
        # evita somar matches sem quantidade (que costumam ser linhas de cálculo/explicação).
        if match.group(1):
            encontrou_com_qtd = True
            volume_total_cm3 += vol_linha
        else:
            volume_sem_qtd_cm3 += vol_linha

    if not encontrou_com_qtd:
        volume_total_cm3 += volume_sem_qtd_cm3

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

    # Prioridade: linhas de total (ex.: "Peso real total: 1.358 kg")
    m_total = re.search(
        r"\b(?:peso\s*)?(?:real\s*)?total\b[^\d]{0,20}(\d+(?:[\.,]\d+)*)\s*kg\b",
        texto,
        re.IGNORECASE,
    )
    if m_total:
        v = parse_float_ptbr(m_total.group(1))
        if v is not None:
            return v

    # Preferência: última linha que seja apenas um total em kg (ex.: "(1.358kg)")
    last_simple_total: float | None = None
    for line in texto.splitlines():
        ln = (line or "").strip()
        if not ln:
            continue
        m_simple = re.fullmatch(
            r"\(?\s*(\d+(?:[\.,]\d+)*)\s*kg\s*\)?",
            ln,
            flags=re.IGNORECASE,
        )
        if m_simple:
            v = parse_float_ptbr(m_simple.group(1))
            if v is not None:
                last_simple_total = v
    if last_simple_total is not None:
        return last_simple_total

    # Tenta calcular como a transportadora: (qtd) ... - xxkg => qtd * xx
    per_volume = re.compile(
        r"\(\s*(\d+)\s*\)\s*.*?[-–—:]\s*(\d+(?:[\.,]\d+)*)\s*kg\b",
        re.IGNORECASE,
    )
    soma_calc = 0.0
    encontrados_calc = 0
    for m3 in per_volume.finditer(texto):
        try:
            qtd = int(m3.group(1))
        except ValueError:
            continue
        peso_unit = parse_float_ptbr(m3.group(2))
        if qtd > 0 and peso_unit is not None:
            soma_calc += qtd * peso_unit
            encontrados_calc += 1
    if encontrados_calc > 0:
        return soma_calc

    # Soma todos os pesos explícitos "xxkg" (último fallback)
    re_kg = re.compile(r"(\d+(?:[\.,]\d+)*)\s*kg\b", re.IGNORECASE)
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
