import streamlit as st
from streamlit_option_menu import option_menu

# --- CORES ESTILO SISTEMA CORPORATIVO ---
COLOR_BG = "#FFFFFF"           # Branco puro (elimina sensação de 'sujo')
COLOR_SIDEBAR = "#1A1C22"      # Grafite Profissional
COLOR_GOLD = "#B8860B"         # Dourado King Star
COLOR_TEXT = "#2D2E33"         # Texto Cinza Escuro (Leitura fácil)

CSS_PORTAL = f"""
<style>
    /* Reset total para visual limpo */
    .stApp {{
        background-color: {COLOR_BG};
    }}

    /* Sidebar Estilo Industrial */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SIDEBAR} !important;
        border-right: 1px solid #e0e0e0;
    }}

    /* Foto de Perfil */
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {COLOR_GOLD};
        margin: 0 auto 10px auto; display: block;
    }}

    /* Textos Sidebar */
    .sb-nome {{ color: white; text-align: center; font-weight: 600; margin-bottom: 0; }}
    .sb-cargo {{ color: {COLOR_GOLD}; text-align: center; font-size: 0.8rem; margin-top: 0; font-weight: bold; }}

    /* Cards de Tarefas (Atrasada/Agendada) */
    .stAlert {{
        border-radius: 8px !important;
        border: 1px solid #f0f0f0 !important;
    }}

    /* Botão de Sair - Estilo Minimalista na Base */
    .stButton > button {{
        width: 100%;
        background-color: transparent !important;
        color: #888 !important;
        border: 1px solid #444 !important;
    }}
    .stButton > button:hover {{
        color: white !important;
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
        "color": "#CCC", "font-size": "14px", "text-align": "left", 
        "margin": "5px", "--hover-color": "#333"
    },
    "nav-link-selected": {
        "background-color": COLOR_GOLD, "color": "white", "font-weight": "bold"
    }
}

# --- FUNÇÕES ---
def configurar_pagina():
    # Isso força o Streamlit a limpar o cache visual e aplicar o novo layout
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    with st.sidebar:
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-nome">{user_info.get("nome", "Usuário")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-cargo">{user_info.get("cargo", "Analista")}</p>', unsafe_allow_html=True)
        
        st.divider()

        escolha = option_menu(
            menu_title=None, options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU
        )
        
        st.write("") 
        if st.button("Sair do Hub"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha

# --- CORREÇÃO DO ERRO DE KEYERROR NO SEU ARQUIVO central.py ---
# Na sua função de exibir usuários, substitua a linha do erro por esta lógica:
# info.get('depto', 'N/A') -> Isso evita que o app trave se a chave não existir.
