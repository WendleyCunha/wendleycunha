import streamlit as st
from streamlit_option_menu import option_menu

# --- LÓGICA DE TEMA DINÂMICO ---
if "tema_dark" not in st.session_state:
    st.session_state.tema_dark = True  # Começa no Dark por padrão

# --- DEFINIÇÃO DE CORES ADAPTATIVAS ---
if st.session_state.tema_dark:
    COLOR_BG = "#121212"
    COLOR_SIDEBAR = "#1A1C22"
    COLOR_TEXT = "#FFFFFF"
    COLOR_MENU_TEXT = "#CCC"
    COLOR_MENU_HOVER = "#333"
else:
    COLOR_BG = "#FFFFFF"
    COLOR_SIDEBAR = "#F8F9FA"
    COLOR_TEXT = "#2D2E33"
    COLOR_MENU_TEXT = "#343A40"
    COLOR_MENU_HOVER = "#E9ECEF"

COLOR_GOLD = "#B8860B"

CSS_PORTAL = f"""
<style>
    .stApp {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
    }}

    [data-testid="stSidebar"] {{
        background-color: {COLOR_SIDEBAR} !important;
        border-right: 1px solid rgba(0,0,0,0.1);
    }}

    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {COLOR_GOLD};
        margin: 0 auto 10px auto; display: block;
    }}

    .sb-nome {{ color: {COLOR_TEXT}; text-align: center; font-weight: 600; margin-bottom: 0; }}
    .sb-cargo {{ color: {COLOR_GOLD}; text-align: center; font-size: 0.8rem; margin-top: 0; font-weight: bold; }}

    /* Botão de Sair Minimalista */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        background-color: transparent !important;
        color: {COLOR_MENU_TEXT} !important;
        border: 1px solid rgba(128,128,128,0.3) !important;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        color: {COLOR_GOLD} !important;
        border-color: {COLOR_GOLD} !important;
    }}
</style>
"""

# --- DICIONÁRIOS ---
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

ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": "#888", "font-size": "16px"}, 
    "nav-link": {
        "color": COLOR_MENU_TEXT, "font-size": "14px", "text-align": "left", 
        "margin": "5px", "--hover-color": COLOR_MENU_HOVER
    },
    "nav-link-selected": {
        "background-color": COLOR_GOLD, "color": "white", "font-weight": "bold"
    }
}

# --- FUNÇÕES ---
def configurar_pagina():
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        # Foto e Informações
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-nome">{user_info.get("nome", "Usuário")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-cargo">{user_info.get("cargo", "Analista")}</p>', unsafe_allow_html=True)
        
        st.divider()

        # Menu Principal
        escolha = option_menu(
            menu_title=None, options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU
        )
        
        st.divider()
        
        # --- SELETOR DE TEMA NO RODAPÉ DA SIDEBAR ---
        st.write("Configurações")
        tipo_tema = "🌙 Dark Mode" if st.session_state.tema_dark else "☀️ Light Mode"
        
        if st.toggle(tipo_tema, value=st.session_state.tema_dark):
            if not st.session_state.tema_dark:
                st.session_state.tema_dark = True
                st.rerun()
        else:
            if st.session_state.tema_dark:
                st.session_state.tema_dark = False
                st.rerun()

        if st.button("Sair do Hub"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha

# --- NOTA TÉCNICA PARA O ARQUIVO central.py ---
# Para resolver o KeyError 'depto', localize a linha do erro e mude para:
# info.get('depto', 'N/A')
