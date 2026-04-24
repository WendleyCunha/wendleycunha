import streamlit as st

# 1. CONFIGURAÇÃO DE PÁGINA
def configurar_pagina():
    st.set_page_config(
        page_title="Hub King Star | Master",
        layout="wide",
        page_icon="👑"
    )

# 2. ESTILO CSS PREMIUM (O que o seu Main espera)
CSS_PREMIUM = """
    <style>
    .stApp { background-color: #f8fafc; }
    .gold-title {
        color: #002366;
        text-align: center;
        font-weight: bold;
        letter-spacing: 2px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .profile-pic {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #D4AF37;
        margin: 0 auto 10px auto;
        display: block;
    }
    /* Estilo para os cards que você usa na Home */
    .reminder-card {
        background: white; padding: 15px; border-radius: 10px;
        border-left: 5px solid #ef4444; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
"""

# 3. MAPA DE MÓDULOS (IDs que batem com as permissões do Banco)
MAPA_MODULOS_MESTRE = {
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets"
}

# 4. MAPA DE ÍCONES (Para o option_menu)
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
