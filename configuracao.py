import streamlit as st
from streamlit_option_menu import option_menu

# 1. Cores Oficiais
AZUL_MARINHO = "#002366"
DOURADO_KING = "#B8860B"
BRANCO_PURO = "#FFFFFF"
CINZA_CLARO = "rgba(255, 255, 255, 0.7)"

# 2. Dicionários de Dados (O QUE ESTAVA FALTANDO)
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

# 3. Estilos CSS e Menu
CSS_PORTAL = f"""
    <style>
    .stApp {{ background-color: #f1f5f9; }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_MARINHO} !important; }}
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p {{ color: {BRANCO_PURO} !important; }}
    div.stButton > button:first-child {{
        background-color: {DOURADO_KING} !important;
        color: {BRANCO_PURO} !important;
        border: none; font-weight: bold;
    }}
    .profile-pic {{
        width: 110px; height: 110px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 10px auto; display: block;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }}
    </style>
"""

ESTILO_MENU = {
    "container": {"padding": "5px!important", "background-color": "transparent"},
    "icon": {"color": BRANCO_PURO, "font-size": "18px"}, 
    "nav-link": {
        "color": CINZA_CLARO, "font-size": "15px", "text-align": "left", "margin": "5px",
        "--hover-color": "rgba(184, 134, 11, 0.2)"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, "color": BRANCO_PURO, "font-weight": "bold"
    },
}

# 4. Funções de Interface
def configurar_pagina():
    st.set_page_config(page_title="Hub King Star | Master", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        foto_url = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto_url}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center; color:{BRANCO_PURO}; margin-bottom:0;'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{DOURADO_KING}; font-weight:bold;'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
        st.divider()
        escolha = option_menu(
            menu_title=None, options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            menu_icon="cast", default_index=0, styles=ESTILO_MENU
        )
        st.markdown("---")
        if st.button("Logoff 🚪", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
    return escolha
