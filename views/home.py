import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modulos import database as db

def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0: return "0min"
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"

def exibir(user_info):
    st.title(f"Olá, {user_info['nome']}! 👋")
    # ... (Todo o código das tabs: Esforço, Pendentes, Agenda, Novo que estava na main)
