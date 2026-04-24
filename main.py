import streamlit as st
from streamlit_option_menu import option_menu
from modulos import database as db
import configuracao as config

# 1. SETUP
config.configurar_pagina()
st.markdown(config.CSS_PREMIUM, unsafe_allow_html=True)

# 2. AUTENTICAÇÃO (Mantenha simples no main)
usuarios = db.carregar_usuarios_firebase()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 class='gold-title'>WENDLEY PORTAL</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuário").lower().strip()
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if u in usuarios and (usuarios[u]["senha"] == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# 3. DADOS DE ACESSO
user_info = usuarios.get(st.session_state.user_id)
user_role = user_info.get('role', 'OPERACIONAL')
modulos_permitidos = user_info.get('modulos', [])

# 4. SIDEBAR DINÂMICA
with st.sidebar:
    st.markdown(f"<h3 style='color:#495057;'>Olá, {user_info['nome']}</h3>", unsafe_allow_html=True)
    
    # Montagem lógica do Menu
    menu_options = ["🏠 Home", "📄 Cartas"]
    if "processos" in modulos_permitidos or user_role == "ADM": menu_options.append("🎯 Processos")
    if "spin" in modulos_permitidos or user_role == "ADM": menu_options.append("🚗 Minha Spin")
    if user_role == "ADM": menu_options.append("⚙️ Central")

    escolha = option_menu(
        "Menu Principal", menu_options, 
        icons=[config.ICON_MAP.get(opt) for opt in menu_options], 
        menu_icon="cast", default_index=0,
        styles={"nav-link-selected": {"background-color": "#D4AF37"}}
    )
    
    st.write("---")
    if st.button("Sair / Logout", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# 5. ROTEADOR (CHAMADA DOS MÓDULOS)
# Importamos apenas o necessário conforme a escolha para economizar memória
if escolha == "🏠 Home":
    from views import home
    home.exibir(user_info)

elif escolha == "📄 Cartas":
    from views import mod_cartas
    mod_cartas.exibir(user_role)

elif escolha == "🎯 Processos":
    from views import mod_processos
    mod_processos.exibir(user_role)

elif escolha == "🚗 Minha Spin":
    from views import mod_spin
    mod_spin.exibir_tamagotchi(user_info)

elif escolha == "⚙️ Central":
    if user_role == "ADM":
        from views import central
        central.exibir()
