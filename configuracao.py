import streamlit as st
from streamlit_option_menu import option_menu

# --- NOVAS CORES (SIDEBAR CLARA) ---
AZUL_AGUA = "#E0F7FA"       # Cor bem clarinha, água
AZUL_TEXTO = "#001a3d"      # Azul marinho para contraste no texto
DOURADO_KING = "#B8860B"    # Dourado oficial
BRANCO = "#FFFFFF"

CSS_PORTAL = f"""
<style>
    /* Fundo da aplicação */
    .stApp {{ background-color: #f4f7f9; }}
    
    /* Sidebar com cor Água e remoção de sombras/blocos */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarNav"] {{
        background-color: {AZUL_AGUA} !important;
    }}

    /* Ajuste de cor para divisores na sidebar clara */
    [data-testid="stSidebar"] hr {{
        border: 0;
        border-top: 1px solid rgba(0,0,0,0.1);
    }}

    /* Foto de Perfil */
    .profile-pic {{
        width: 110px; height: 110px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 10px auto; display: block;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }}

    /* Botão de Sair Ajustado para fundo claro */
    [data-testid="stSidebar"] .stButton > button {{
        background-color: transparent !important;
        color: {AZUL_TEXTO} !important;
        border: 1px solid rgba(0,0,0,0.2) !important;
        border-radius: 8px;
        width: 100%;
    }}
</style>
"""

# --- DADOS MESTRE ---
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

# Estilo do Menu adaptado para fundo claro
ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": AZUL_TEXTO, "font-size": "18px"}, 
    "nav-link": {
        "color": AZUL_TEXTO, 
        "font-size": "14px", 
        "text-align": "left", 
        "margin": "5px", 
        "--hover-color": "rgba(0,0,0,0.05)"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, 
        "color": BRANCO, 
        "font-weight": "bold"
    }
}

# --- FUNÇÕES ---
def configurar_pagina():
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        
        # Texto agora em Azul Marinho para leitura no fundo claro
        st.markdown(f"<h3 style='text-align:center; color:{AZUL_TEXTO};'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{DOURADO_KING}; font-weight:bold;'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
        
        st.divider()

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
