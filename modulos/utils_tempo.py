from datetime import datetime
import pytz

TZ_BR = pytz.timezone("America/Sao_Paulo")

def agora_br():
    """Retorna datetime atual no fuso de São Paulo (tz-aware)."""
    return datetime.now(TZ_BR)

def agora_iso():
    """Retorna string ISO do momento atual em São Paulo."""
    return agora_br().isoformat()

def parse_dt_safe(valor):
    """
    Tenta converter qualquer string de data/hora para datetime tz-aware (SP).
    Retorna None em caso de falha.
    """
    if not valor:
        return None
    try:
        if isinstance(valor, datetime):
            if valor.tzinfo is None:
                return TZ_BR.localize(valor)
            return valor.astimezone(TZ_BR)
        # Remove microsegundos extras e tenta parsear
        dt = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return TZ_BR.localize(dt)
        return dt.astimezone(TZ_BR)
    except Exception:
        return None
