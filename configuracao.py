# configuracao.py
import streamlit as st

def configurar_pagina():
    st.set_page_config(page_title="Hub King Star | Premium", layout="wide", page_icon="👑")

# Estilo Premium isolado
CSS_PREMIUM = """
    <style>
    [data-testid="stSidebar"] { background-color: #F8F9FA; }
    div.stButton > button:first-child {
        background-color: #D4AF37; color: white; border: none; border-radius: 8px; transition: 0.3s;
    }
    .gold-title {
        text-align: center; color: #D4AF37; font-family: 'Trebuchet MS', sans-serif; font-weight: bold;
    }
    /* Estilos das abas e cards podem vir para cá também */
    </style>
"""

# Simplificamos os ícones para bater com o menu dinâmico
ICON_MAP = {
    "🏠 Home": "house",
    "📄 Cartas": "file-earmark-text",
    "🎯 Processos": "diagram-3",
    "🚗 Minha Spin": "car-front-fill",
    "⚙️ Central": "shield-lock"
}
