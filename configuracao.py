import streamlit as st

# Cores Oficiais
AZUL_MARINHO = "#002366"
DOURADO_KING = "#B8860B"

CSS_PORTAL = f"""
    <style>
    .stApp {{ background-color: #f8fafc; }}
    
    /* Sidebar Marinho */
    [data-testid="stSidebar"] {{
        background-color: {AZUL_MARINHO} !important;
    }}

    /* Botões em Dourado */
    div.stButton > button:first-child {{
        background-color: {DOURADO_KING} !important;
        color: white !important;
        border: none;
    }}

    /* Estilo da Foto de Perfil */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 0 auto 10px auto; display: block;
    }}
    </style>
"""

# Identificadores que o usuário tem no Firebase (ex: "cartas", "spin")
MAPA_MODULOS_MESTRE = {
    "Manutenção": "manutencao",
    "Processos": "processos",
    "RH Docs": "rh",
    "Operação": "operacao",
    "Minha Spin": "spin",
    "Cartas": "cartas"
}

ICON_MAP = {
    "Home": "house",
    "Manutenção": "tools",
    "Processos": "diagram-3",
    "RH Docs": "file-earmark-text",
    "Operação": "box-seam",
    "Minha Spin": "car-front-fill",
    "Cartas": "envelope-paper",
    "Central de Comando": "shield-lock"
}

ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": "white", "font-size": "18px"}, 
    "nav-link": {
        "color": "rgba(255,255,255,0.7)", 
        "font-size": "14px", 
        "text-align": "left", 
        "margin":"5px"
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
