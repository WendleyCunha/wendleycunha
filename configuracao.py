import streamlit as st

# Cores da Identidade Visual
AZUL_MARINHO = "#002366"
DOURADO_KING = "#B8860B" # Tom Gold/Mostarda

CSS_PORTAL = f"""
    <style>
    .stApp {{ background-color: #f8fafc; }}
    
    /* Cor do botão principal */
    div.stButton > button:first-child {{
        background-color: {AZUL_MARINHO};
        color: white;
        border-radius: 8px;
    }}
    
    /* Foto de perfil na sidebar */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 0 auto 10px auto; display: block;
    }}
    </style>
"""

MAPA_MODULOS_MESTRE = {
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
}

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

# Estilo do Menu Lateral
ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": DOURADO_KING, "font-size": "18px"}, 
    "nav-link": {"color": "white", "font-size": "14px", "text-align": "left", "margin":"5px"},
    "nav-link-selected": {"background-color": DOURADO_KING, "color": "white"},
}

def configurar_pagina():
    st.set_page_config(page_title="Hub King Star | Master", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)
    # Força a sidebar a ser escura (Marinho)
    st.markdown(f'<style>[data-testid="stSidebar"] {{ background-color: {AZUL_MARINHO}; }}</style>', unsafe_allow_html=True)
