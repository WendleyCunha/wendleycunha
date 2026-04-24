import streamlit as st
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DE CORES PROFISSIONAIS ---
COR_FUNDO_PAGINA = "#F0F2F6"  # Cinza claro de fundo para destacar os cards brancos
COR_SIDEBAR = "#1E1E26"       # Grafite escuro profissional
DOURADO_KING = "#B8860B"      # Dourado oficial
AZUL_DARK = "#001a3d"         # Texto principal
BRANCO = "#FFFFFF"

CSS_PORTAL = f"""
<style>
    /* Fundo principal da aplicação */
    .stApp {{
        background-color: {COR_FUNDO_PAGINA};
    }}

    /* Estilização da Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COR_SIDEBAR} !important;
    }}

    /* Cards Brancos (Padrão de mercado para legibilidade) */
    div[data-testid="stVerticalBlock"] > div > div > div[dir="ltr"] {{
        background-color: {BRANCO};
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }}

    /* Foto de Perfil */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 10px auto; display: block;
    }}

    /* Títulos e Textos na Sidebar */
    .sidebar-name {{
        color: {BRANCO}; text-align: center; margin-bottom: 0px; font-size: 1.2rem;
    }}
    .sidebar-job {{
        color: {DOURADO_KING}; text-align: center; font-weight: bold; margin-top: 0px;
    }}

    /* Botão de Sair (Estilo Clean) */
    .stButton > button {{
        width: 100%;
        background-color: transparent !important;
        color: {BRANCO} !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        transition: 0.3s;
    }}
    .stButton > button:hover {{
        background-color: {DOURADO_KING} !important;
        color: {BRANCO} !important;
        border: none !important;
    }}

    /* Ajuste para inputs e áreas de texto */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        background-color: {BRANCO} !important;
        color: {AZUL_DARK} !important;
    }}
</style>
"""

# --- DICIONÁRIOS DE SUPORTE ---
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

# Estilo do Menu Lateral (Dark Mode Sidebar)
ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": "#8E8E93", "font-size": "18px"}, 
    "nav-link": {
        "color": BRANCO, "font-size": "14px", "text-align": "left", 
        "margin": "5px", "--hover-color": "rgba(255,255,255,0.05)"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, "color": BRANCO, "font-weight": "bold"
    }
}

# --- FUNÇÕES CORE ---
def configurar_pagina():
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        # Perfil
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f'<p class="sidebar-name">{user_info.get("nome", "Usuário")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sidebar-job">{user_info.get("cargo", "Analista")}</p>', unsafe_allow_html=True)
        
        st.divider()

        # Menu de Navegação
        escolha = option_menu(
            menu_title=None, options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU
        )
        
        st.write("") 
        if st.button("Sair 🚪"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha
