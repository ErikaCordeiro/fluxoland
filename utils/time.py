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
