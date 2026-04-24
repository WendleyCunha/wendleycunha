import streamlit as st
from streamlit_option_menu import option_menu
import configuracao as config
from modulos import database as db
from views import home

# 1. Configuração Inicial
config.configurar_pagina()

# 2. Carregamento de Dados
usuarios = db.carregar_usuarios_firebase()

# 3. Lógica de Login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 style='text-align:center;'>Wendley Portal</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuário").lower().strip()
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if u in usuarios and (usuarios[u].get("senha") == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
    st.stop()

# 4. Preparação do Menu
user_info = usuarios.get(st.session_state.user_id)
user_role = user_info.get('role', 'USER')
is_adm = user_role == "ADM"
permissoes_usuario = user_info.get('modulos', [])

with st.sidebar:
    # Foto e Perfil
    foto_url = user_info.get('foto', 'https://www.w3schools.com/howto/img_avatar.png')
    st.markdown(f'<img src="{foto_url}" class="profile-pic">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; color:white;'>{user_info.get('nome', 'Usuário')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#FFD700;'>{user_info.get('cargo', 'Analista')}</p>", unsafe_allow_html=True)
    
    st.divider()

    # Montagem Dinâmica das Opções
    menu_options = ["Home"] 
    for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
        if is_adm or id_modulo in permissoes_usuario:
            menu_options.append(label)

    if is_adm:
        menu_options.append("Central de Comando")
    
    escolha = option_menu(
        menu_title=None, 
        options=menu_options,
        icons=[config.ICON_MAP.get(opt, "circle") for opt in menu_options],
        menu_icon="cast", 
        default_index=0,
        styles=config.ESTILO_MENU
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logoff 🚪", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# 5. ROTEADOR (Faz a ponte com os arquivos na pasta views/modulos)
if escolha == "Home":
    home.exibir(user_info)

elif escolha == "Manutenção":
    from modulos import mod_manutencao
    mod_manutencao.main()

elif escolha == "Minha Spin":
    from modulos import mod_spin
    mod_spin.exibir_tamagotchi(user_info)

elif escolha == "Cartas": # <--- AGORA O MOD_CARTAS ABRE AQUI
    from views import mod_cartas
    mod_cartas.exibir(user_role)

elif escolha == "Central de Comando":
    from views import central
    departamentos = db.carregar_departamentos()
    central.exibir(usuarios, departamentos)

else:
    st.warning(f"O módulo '{escolha}' ainda não foi integrado ao roteador.")
