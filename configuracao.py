import streamlit as st

# Paleta King Star
AZUL_MARINHO = "#002366"
DOURADO_KING = "#B8860B" 

CSS_PORTAL = f"""
    <style>
    /* Fundo geral mais limpo */
    .stApp {{ background-color: #F4F7F9; }}
    
    /* Botão de login dourado como na sua imagem */
    div.stButton > button:first-child {{
        background-color: {DOURADO_KING} !important;
        color: white !important;
        font-weight: bold;
        border: none;
    }}

    /* Estilo da foto de perfil */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 0 auto 10px auto; display: block;
    }}
    </style>
"""

# 1. REMOVA OS EMOJIS DAQUI (isso evita a duplicidade)
MAPA_MODULOS_MESTRE = {
    "Manutenção": "manutencao",
    "Processos": "processos",
    "RH Docs": "rh",
    "Operação": "operacao",
    "Minha Spin": "spin",
    "Passagens": "passagens",
    "Tickets": "tickets",
    "Cartas": "cartas" # Adicionado para o mod_cartas
}

# 2. DEFINA OS ÍCONES AQUI (Bootstrap Icons)
ICON_MAP = {
    "Home": "house",
    "Manutenção": "tools",
    "Processos": "diagram-3",
    "RH Docs": "file-earmark-text",
    "Operação": "box-seam",
    "Minha Spin": "car-front-fill",
    "Passagens": "bus-front",
    "Tickets": "ticket-perforated",
    "Cartas": "envelope-paper",
    "Central de Comando": "shield-lock"
}

ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": AZUL_MARINHO},
    "icon": {"color": "white", "font-size": "18px"}, 
    "nav-link": {
        "color": "rgba(255,255,255,0.7)", 
        "font-size": "14px", 
        "text-align": "left", 
        "margin":"5px",
        "--hover-color": "rgba(255,255,255,0.1)"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, 
        "color": "white",
        "font-weight": "bold"
    },
}

def configurar_pagina():
    st.set_page_config(page_title="Hub King Star | Master", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)
    st.markdown(f'<style>[data-testid="stSidebar"] {{ background-color: {AZUL_MARINHO} !important; }}</style>', unsafe_allow_html=True)
