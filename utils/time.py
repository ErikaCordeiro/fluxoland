from datetime import datetime, timezone

def tempo_relativo(data: datetime) -> str:
    if not data:
        return ""

    agora = datetime.now(timezone.utc)
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)

    diff = agora - data
    segundos = int(diff.total_seconds())

    if segundos < 60:
        return "agora mesmo"

    minutos = segundos // 60
    if minutos < 60:
        return f"{minutos} min atrás"

    horas = minutos // 60
    if horas < 24:
        return f"{horas}h atrás"

    dias = horas // 24
    return f"{dias}d atrás"

def time_ago(data: datetime) -> str:
    """Retorna tempo relativo formatado como 'Atualizado há X'"""
    if not data:
        return ""

    agora = datetime.now(timezone.utc)
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)

    diff = agora - data
    segundos = int(diff.total_seconds())

    if segundos < 60:
        return "Atualizado agora"

    minutos = segundos // 60
    if minutos == 1:
        return "Atualizado há 1 minuto"
    if minutos < 60:
        return f"Atualizado há {minutos} minutos"

    horas = minutos // 60
    if horas == 1:
        return "Atualizado há 1 hora"
    if horas < 24:
        return f"Atualizado há {horas} horas"

    dias = horas // 24
    if dias == 1:
        return "Atualizado há 1 dia"
    return f"Atualizado há {dias} dias"
