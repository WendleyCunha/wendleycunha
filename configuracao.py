import streamlit as st

from streamlit_option_menu import option_menu



# CORES EXECUTIVAS KING STAR

COLOR_BG = "#FFFFFF"           # Branco (Fundo principal)

COLOR_SIDEBAR = "#1A1C22"      # Grafite (Sidebar)

COLOR_GOLD = "#B8860B"         # Dourado

COLOR_TEXT = "#2D2E33"         # Cinza escuro (Texto)



CSS_ESTAVEL = f"""

<style>

    /* Forçar fundo branco e texto escuro em todo o app */

    .stApp {{

        background-color: {COLOR_BG} !important;

        color: {COLOR_TEXT} !important;

    }}



    /* Estilização da Sidebar */

    [data-testid="stSidebar"] {{

        background-color: {COLOR_SIDEBAR} !important;

    }}



    /* Garantir que títulos e textos fora da sidebar sejam pretos */

    h1, h2, h3, p, span, label {{

        color: {COLOR_TEXT} !important;

    }}



    /* Foto de Perfil */

    .profile-pic {{

        width: 100px; height: 100px; border-radius: 50%;

        object-fit: cover; border: 3px solid {COLOR_GOLD};

        margin: 0 auto 10px auto; display: block;

    }}



    .sb-nome {{ color: white !important; text-align: center; font-weight: 600; margin-bottom: 0; }}

    .sb-cargo {{ color: {COLOR_GOLD} !important; text-align: center; font-size: 0.8rem; margin-top: 0; font-weight: bold; }}



    /* Cards da Agenda */

    .stAlert {{

        background-color: #F8F9FA !important;

        border: 1px solid #E9ECEF !important;

        color: {COLOR_TEXT} !important;

    }}

</style>

"""



MAPA_MODULOS_MESTRE = {

    "Manutenção": "manutencao", "Processos": "processos",

    "RH Docs": "rh", "Operação": "operacao",

    "Minha Spin": "spin", "Cartas": "cartas"

}



def configurar_pagina():

    st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")

    st.markdown(CSS_ESTAVEL, unsafe_allow_html=True)



def desenhar_sidebar(user_info, menu_options):

    # 1. Mapeamento de ícones (Centralizado e fácil de dar manutenção)

    mapa_icones = {

        "Home": "house",

        "Manutenção": "tools",

        "Processos": "diagram-3",

        "RH Docs": "file-text",

        "Operação": "box",

        "Minha Spin": "car",

        "Cartas": "envelope",

        "Central de Comando": "shield-lock"

    }



    # 2. Gerar lista de ícones DINÂMICA baseada apenas no que vai aparecer

    # Se a opção não estiver no mapa, ele usa "circle" como padrão

    icones_dinamicos = [mapa_icones.get(opt, "circle") for opt in menu_options]



    with st.sidebar:

        foto = user_info.get('foto') or 'https://www.w3schools.com/howto/img_avatar.png'

        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)

        st.markdown(f'<p class="sb-nome">{user_info.get("nome", "Usuário")}</p>', unsafe_allow_html=True)

        st.markdown(f'<p class="sb-cargo">{user_info.get("cargo", "Analista")}</p>', unsafe_allow_html=True)

        

        st.divider()



        # 3. O componente agora recebe duas listas de mesmo tamanho sempre

        escolha = option_menu(

            menu_title=None, 

            options=menu_options,

            icons=icones_dinamicos, 

            styles={

                "container": {"background-color": "transparent"},

                "nav-link": {"color": "#CCC", "font-size": "14px", "text-align": "left"},

                "nav-link-selected": {"background-color": COLOR_GOLD, "color": "white"}

            }

        )

        

        if st.button("Sair do Sistema"):

            st.session_state.autenticado = False

            st.rerun()

            

    return escolha
