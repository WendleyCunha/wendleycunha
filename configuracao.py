import streamlit as st
from streamlit_option_menu import option_menu

# --- CORES FIXAS (SIMPLICIDADE E FOCO) ---
COLOR_BG = "#FFFFFF"           # Fundo Branco Puro
COLOR_SIDEBAR = "#1A1C22"      # Sidebar Grafite King Star
COLOR_GOLD = "#B8860B"         # Dourado Oficial
COLOR_TEXT_MAIN = "#2D2E33"    # Texto Escuro para leitura

CSS_PORTAL = f"""
<style>
    /* Forçar fundo branco na área de trabalho */
    .stApp {{
        background-color: {COLOR_BG} !important;
    }}

    /* Sidebar Fixa e Profissional */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SIDEBAR} !important;
        min-width: 260px !important;
    }}

    /* Foto de Perfil */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {COLOR_GOLD};
        margin: 0 auto 10px auto; display: block;
    }}

    /* Textos da Sidebar */
    .sb-nome {{ color: white !important; text-align: center; font-weight: 600; margin-bottom: 0; }}
    .sb-cargo {{ color: {COLOR_GOLD} !important; text-align: center; font-size: 0.85rem; margin-top: 0; font-weight: bold; }}

    /* Limpeza de botões */
    .stButton > button {{
        width: 100%;
        border-radius: 5px;
        background-color: transparent;
        color: #888 !important;
        border: 1px solid #444 !important;
        transition: 0.3s;
    }}
    .stButton > button:hover {{
        color: white !important;
        border-color: {COLOR_GOLD} !important;
        background-color: {COLOR_GOLD} !important;
    }}
</style>
"""

# --- DICIONÁRIOS MESTRE ---
MAPA_MODULOS_MESTRE = {
    "Manutenção": "manutencao", "Processos": "processos",
    "RH Docs": "rh", "Operação": "operacao",
    "Minha Spin": "spin", "Cartas": "cartas"
}

ICON_MAP = {
    "Home": "house", "Manutenção": "tools", "Processos": "diagram-3",
    "RH Docs": "file-earmark-text", "Operação": "box-seam",
    "Minha Spin": "car-front-fill", "Cartas": "envelope-paper",
    "Central de Comando": "shield-lock"
}

# Estilo do Menu lateral fixo
ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": "#888", "font-size": "16px"}, 
    "nav-link": {
        "color": "#CCC", "font-size": "14px", "text-align": "left", 
        "margin": "5px", "--hover-color": "#333"
    },
    "nav-link-selected": {
        "background-color": COLOR_GOLD, "color": "white", "font-weight": "bold"
    }
}

# --- FUNÇÕES CORE ---
def configurar_pagina():
    # Configuração de layout ampla e título
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        # Foto e Identificação
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-nome">{user_info.get("nome", "Usuário")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-cargo">{user_info.get("cargo", "Analista")}</p>', unsafe_allow_html=True)
        
        st.divider()

        # Menu de Navegação
        escolha = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU,
            default_index=0
        )
        
        # Espaço e Botão de Logout
        st.write("") 
        if st.button("Sair do Sistema 🚪"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha
