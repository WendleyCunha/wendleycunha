# configuracao.py
import streamlit as st

def configurar_pagina():
    st.set_page_config(
        page_title="Hub King Star | Premium", 
        layout="wide", 
        page_icon="👑"
    )

# Estilo Premium isolado
CSS_PREMIUM = """
    <style>
    /* Fundo da App */
    .stApp { background-color: #f8fafc; }
    
    /* Customização da Sidebar */
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #e2e8f0; }
    
    /* Botões Padrão (Dourado King) */
    div.stButton > button:first-child {
        background-color: #D4AF37; 
        color: white; 
        border: none; 
        border-radius: 8px; 
        transition: 0.3s;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #b8962d;
        border: none;
        color: white;
    }

    /* Títulos e Cards */
    .gold-title {
        text-align: center; 
        color: #D4AF37; 
        font-family: 'Trebuchet MS', sans-serif; 
        font-weight: bold;
    }
    .profile-pic {
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid #D4AF37;
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

# Mapeamento de Módulos (ID interno vs Nome do Menu)
MAPA_MODULOS_MESTRE = {
    "🏠 Home": "home",
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
}

# Ícones para o option_menu
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
