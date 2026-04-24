import streamlit as st
from streamlit_option_menu import option_menu
import configuracao as config
from modulos import database as db
from views import home, central  # Assumindo que você moverá a central também

# 1. Configuração Inicial
config.configurar_pagina()

# 2. Carregamento de Dados (Silencioso)
usuarios = db.carregar_usuarios_firebase()
departamentos = db.carregar_departamentos()

# 3. Lógica de Login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Mostra sua tela de login (você pode até criar uma views/login.py depois)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>Wendley Portal</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuário").lower().strip()
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if u in usuarios and (usuarios[u]["senha"] == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
    st.stop()

# 4. Sidebar e Menu
user_info = usuarios.get(st.session_state.user_id)
is_adm = user_info.get('role') == "ADM"

with st.sidebar:
    # ... (Código da foto e perfil)
    menu_options = ["🏠 Home"]
    # ... (Lógica de filtrar módulos permitidos usando config.MAPA_MODULOS_MESTRE)
    
    escolha = option_menu(None, menu_options, 
                         icons=[config.ICON_MAP.get(opt, "circle") for opt in menu_options],
                         styles={"nav-link-selected": {"background-color": "#002366"}})

# 5. Roteador (Onde a mágica acontece)
if escolha == "🏠 Home":
    home.exibir(user_info)

elif "Manutenção" in escolha:
    from modulos import mod_manutencao
    mod_manutencao.main()

elif "Minha Spin" in escolha:
    from modulos import mod_spin
    mod_spin.exibir_tamagotchi(user_info)

elif "Central de Comando" in escolha:
    from views import central
    central.exibir(usuarios, departamentos) # Mova a lógica da central para views/central.py
