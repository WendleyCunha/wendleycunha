import streamlit as st
from streamlit_option_menu import option_menu

# --- NOVA PALETA KING STAR PREMIUM (DARK) ---
COR_FUNDO_APP = "#0E1117"     # Fundo padrão Dark
COR_SIDEBAR = "#1A1C23"       # Cinza escuro (conforme imagem Operacoes G2)
DOURADO_KING = "#D4AF37"      # Dourado Metálico
BRANCO = "#FFFFFF"
CINZA_TEXTO = "#A0A0A0"

CSS_PORTAL = f"""
<style>
    /* Fundo da aplicação */
    .stApp {{ 
        background-color: {COR_FUNDO_APP}; 
    }}
    
    /* Sidebar Dark Profissional */
    [data-testid="stSidebar"] {{
        background-color: {COR_SIDEBAR} !important;
        border-right: 1px solid rgba(212, 175, 55, 0.1);
    }}

    /* Ajuste de cor para divisores no tema escuro */
    [data-testid="stSidebar"] hr {{
        border-top: 1px solid rgba(255,255,255,0.1) !important;
    }}

    /* Foto de Perfil com brilho dourado sutil */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 2px solid {DOURADO_KING};
        margin: 10px auto; display: block;
        box-shadow: 0px 0px 15px rgba(212, 175, 55, 0.2);
    }}

    /* Botão de Sair Estilizado */
    [data-testid="stSidebar"] .stButton > button {{
        background-color: transparent !important;
        color: {BRANCO} !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 8px;
        width: 100%;
        transition: 0.3s;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: {DOURADO_KING} !important;
        color: black !important;
        border: none !important;
    }}
</style>
"""

# --- DADOS MESTRE (INTEGRIDADE MANTIDA) ---
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

# Estilo do Menu adaptado para o Tema Dark
ESTILO_MENU = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": CINZA_TEXTO, "font-size": "17px"}, 
    "nav-link": {
        "color": BRANCO, 
        "font-size": "14px", 
        "text-align": "left", 
        "margin": "5px", 
        "--hover-color": "rgba(212, 175, 55, 0.1)"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, 
        "color": "black", 
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
        
        # Nome em Branco e Cargo em Dourado para destaque
        st.markdown(f"<h3 style='text-align:center; color:{BRANCO}; margin-bottom: 0;'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{DOURADO_KING}; font-weight:bold; margin-top: 0;'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
        
        st.divider()

        escolha = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU
        )
        
        st.write("") 
        if st.button("Sair 🚪"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha
