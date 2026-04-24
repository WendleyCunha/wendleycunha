# configuracao.py
import streamlit as st

# =========================================================
# CONFIGURAÇÕES TÉCNICAS E VISUAIS
# =========================================================

def configurar_pagina():
    st.set_page_config(
        page_title="Hub King Star | Master", 
        layout="wide", 
        page_icon="👑"
    )

# Mapa de tradução para ID interno
MAPA_MODULOS_MESTRE = {
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
}

# Mapa de ícones do menu
ICON_MAP = {
    "🏠 Home": "house",
    "🏗️ Manutenção": "tools",
    "🎯 Processos": "diagram-3",
    "📄 RH Docs": "file-earmark-text",
    "📊 Operação": "box-seam",
    "🚗 Minha Spin": "car-front-fill",
    "🚌 Passagens": "bus-front",
    "🎫 Tickets": "ticket-perforated",
    "⚙️ Central de Comando": "shield-lock"
}

# Estilos CSS Customizados
CSS_CUSTOM = """
    <style>
    .stApp { background-color: #f8fafc; }
    .profile-pic {
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid #002366;
        margin: 0 auto 10px auto; display: block;
    }
    .reminder-card {
        background: white; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ef4444; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .diary-card {
        background: white; padding: 15px; border-radius: 10px;
        border-left: 5px solid #3b82f6; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
"""
