import streamlit as st
from streamlit_option_menu import option_menu

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
    """Configura o layout básico e o CSS global do portal."""
    st.set_page_config(page_title="Hub King Star | Master", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    """
    Renderiza a foto, nome, cargo e o menu de navegação na lateral.
    Retorna a opção selecionada pelo usuário.
    """
    with st.sidebar:
        # Foto e Perfil do Usuário
        foto_url = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto_url}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center; color:white;'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#FFD700;'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
        
        st.divider()

        # Renderização do Menu Dinâmico
        escolha = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            menu_icon="cast", 
            default_index=0,
            styles=ESTILO_MENU
        )
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Logoff 🚪", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha
