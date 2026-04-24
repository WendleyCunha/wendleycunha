import streamlit as st
from streamlit_option_menu import option_menu

# --- CORES E ESTILO ---
AZUL_MARINHO = "#001a3d" 
DOURADO_KING = "#B8860B"
BRANCO = "#FFFFFF"

CSS_PORTAL = f"""
<style>
    .stApp {{ background-color: #f4f7f9; }}
    [data-testid="stSidebar"] {{ background-color: {AZUL_MARINHO} !important; }}
    
    /* Foto de Perfil */
    .profile-pic {{
        width: 110px; height: 110px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 10px auto; display: block;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }}

    /* Botão Principal */
    div.stButton > button {{
        background-color: {DOURADO_KING} !important;
        color: white !important;
        font-weight: bold; border-radius: 8px;
        border: none; width: 100%;
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

ESTILO_MENU = {
    "container": {"padding": "5px!important", "background-color": "transparent"},
    "icon": {"color": BRANCO, "font-size": "18px"}, 
    "nav-link": {
        "color": "rgba(255,255,255,0.7)", "font-size": "14px", 
        "text-align": "left", "margin": "5px", "--hover-color": "#264653"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, "color": BRANCO, "font-weight": "bold"
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
        st.markdown(f"<h3 style='text-align:center; color:white;'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{DOURADO_KING};'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
        st.divider()

        escolha = option_menu(
            menu_title=None, options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU
        )
        
        st.write("") # Espaçador
        if st.button("Sair 🚪"):
            st.session_state.autenticado = False
            st.rerun()
    return escolha
