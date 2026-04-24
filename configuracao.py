import streamlit as st
from streamlit_option_menu import option_menu

# --- CORES E ESTILO ---
AZUL_MARINHO = "#001a3d" 
DOURADO_KING = "#B8860B"
BRANCO = "#FFFFFF"

CSS_PORTAL = f"""
<style>
    /* Fundo da aplicação */
    .stApp {{ background-color: #f4f7f9; }}
    
    /* Força o fundo da Sidebar e remove containers residuais */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarNav"] {{
        background-color: {AZUL_MARINHO} !important;
    }}

    /* Remove a linha cinza do st.divider para um visual neutro */
    [data-testid="stSidebar"] hr {{
        border: 0;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 1em 0;
    }}

    /* Foto de Perfil */
    .profile-pic {{
        width: 110px; height: 110px; border-radius: 50%;
        object-fit: cover; border: 3px solid {DOURADO_KING};
        margin: 10px auto; display: block;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }}

    /* Botão de Sair Estilo "Ghost" (Fundo transparente, borda fina) */
    [data-testid="stSidebar"] .stButton > button {{
        background-color: transparent !important;
        color: rgba(255,255,255,0.6) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        font-weight: normal;
        border-radius: 8px;
        transition: 0.3s;
        width: 100%;
    }}
    
    [data-testid="stSidebar"] .stButton > button:hover {{
        background-color: rgba(255,255,255,0.05) !important;
        color: {BRANCO} !important;
        border: 1px solid {BRANCO} !important;
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

# Configuração do Option Menu para ser totalmente transparente
ESTILO_MENU = {
    "container": {
        "padding": "0!important", 
        "background-color": "transparent"
    },
    "icon": {"color": BRANCO, "font-size": "18px"}, 
    "nav-link": {
        "color": "rgba(255,255,255,0.7)", 
        "font-size": "14px", 
        "text-align": "left", 
        "margin": "5px", 
        "--hover-color": "rgba(255,255,255,0.1)"
    },
    "nav-link-selected": {
        "background-color": DOURADO_KING, 
        "color": BRANCO, 
        "font-weight": "bold"
    }
}

# --- FUNÇÕES ---
def configurar_pagina():
    """Aplica o layout e o CSS global do portal."""
    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
    st.markdown(CSS_PORTAL, unsafe_allow_html=True)

def desenhar_sidebar(user_info, menu_options):
    """Renderiza a sidebar neutra com azul marinho contínuo."""
    with st.sidebar:
        # Perfil do Usuário
        foto = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center; color:white; margin-bottom:0;'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{DOURADO_KING}; font-weight:bold;'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
        
        st.divider()

        # Menu de Navegação
        escolha = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
            styles=ESTILO_MENU,
            default_index=0
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Botão de Logoff (Estilizado via CSS acima)
        if st.button("Sair do Sistema 🚪"):
            st.session_state.autenticado = False
            st.rerun()
            
    return escolha
