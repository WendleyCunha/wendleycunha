import streamlit as st
from streamlit_option_menu import option_menu

# --- DEFINIÇÃO DE CORES (MODERN CLEAN) ---
COLOR_BG = "#F8F9FA"          # Fundo quase branco, muito limpo
COLOR_SIDEBAR = "#212529"     # Grafite padrão Bootstrap (muito profissional)
COLOR_GOLD = "#B8860B"        # Dourado King Star
COLOR_TEXT_DARK = "#343A40"   # Cinza escuro para leitura perfeita
COLOR_WHITE = "#FFFFFF"

CSS_PORTAL = f"""
<style>
    /* Reset Geral para Limpeza Visual */
    .stApp {{
        background-color: {COLOR_BG};
    }}

    /* Sidebar - Estilo Sólido e Elegante */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SIDEBAR} !important;
        min-width: 280px !important;
    }}

    /* Estilização da Foto de Perfil */
    .profile-container {{
        text-align: center;
        padding: 20px 0;
    }}
    .profile-pic {{
        width: 110px; height: 110px; border-radius: 50%;
        object-fit: cover; border: 3px solid {COLOR_GOLD};
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}

    /* Textos na Sidebar */
    .user-name {{
        color: {COLOR_WHITE}; font-size: 1.1rem; font-weight: 600;
        margin-top: 10px; margin-bottom: 0; text-align: center;
    }}
    .user-job {{
        color: {COLOR_GOLD}; font-size: 0.85rem; font-weight: 500;
        text-transform: uppercase; letter-spacing: 1px; text-align: center;
    }}

    /* Ajuste de Cards e Containers de Conteúdo */
    .stMarkdown, .stButton, .stTextInput {{
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}

    /* Botão de Sair - Minimalista */
    [data-testid="stSidebar"] .stButton > button {{
        background-color: transparent !important;
        color: #ADB5BD !important;
        border: 1px solid #495057 !important;
        border-radius: 6px;
        transition: all 0.3s;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: #C82333 !important;
        color: white !important;
        border-color: #C82333 !important;
    }}

    /* Esconder elementos desnecessários do Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
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

# Estilo do Menu (Bootstrap Standard)
ESTILO_MENU = {
    "container": {"padding": "5px", "background-color": "transparent"},
    "icon": {"color": "#ADB5BD", "font-size": "18px"}, 
    "nav-link": {
        "color": "#E9ECEF", "font-size": "14px", "text-align": "left", 
        "margin": "8px 0px", "border-radius": "8px"
    },
    "nav-link-selected": {
        "background-color": COLOR_GOLD, "color": COLOR_WHITE, "font-weight": "600"
    }
}

# --- FUNÇÕES ---
def configurar_pagina():
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        # Container de Perfil
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f"""
            <div class="profile-container">
                <img src="{foto}" class="profile-pic">
                <p class="user-name">{user_info.get('nome', 'Usuário')}</p>
                <p class="user-job">{user_info.get('cargo', 'Analista')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: #495057; margin-top: 0;'>", unsafe_allow_html=True)

        # Menu de Navegação
        escolha = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU,
            default_index=0
        )
        
        # Espaçador e Botão de Sair
        st.markdown("<div style='flex-grow: 1; min-height: 20vh;'></div>", unsafe_allow_html=True)
        if st.button("Sair do Sistema"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha
