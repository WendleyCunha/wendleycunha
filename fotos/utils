# modulos/utils_tempo.py
from datetime import datetime
import pytz

FUSO_BR = pytz.timezone("America/Sao_Paulo")

def agora_br() -> datetime:
    """Retorna datetime atual no horário de Brasília, sem fuso (naive)."""
    return datetime.now(FUSO_BR).replace(tzinfo=None)

def parse_dt(valor) -> datetime | None:
    """
    Converte qualquer string/datetime para datetime naive (horário de Brasília).
    Nunca lança exceção — retorna None se não conseguir.
    """
    if valor is None:
        return None
    try:
        if isinstance(valor, datetime):
            dt = valor
        else:
            dt = datetime.fromisoformat(str(valor))

        # Se tem fuso, converte para Brasília e remove o fuso
        if dt.tzinfo is not None:
            dt = dt.astimezone(FUSO_BR).replace(tzinfo=None)

        return dt
    except Exception:
        return None  # ← nunca trava, só retorna None

def agora_iso() -> str:
    """Retorna string ISO do momento atual em Brasília. Use para salvar no Firebase."""
    return agora_br().isoformat()

def parse_dt_safe(valor, fallback=None) -> datetime:
    """Como parse_dt mas retorna fallback (default: agora) se falhar."""
    resultado = parse_dt(valor)
    return resultado if resultado is not None else (fallback or agora_br())
