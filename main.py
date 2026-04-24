import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login

# 1. Configuração Inicial (Título, Layout, etc.)
config.configurar_pagina()

# 2. Carregamento de Dados de Usuários
usuarios = db.carregar_usuarios_firebase()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# 3. Lógica de Login (Modularizada)
if not st.session_state.autenticado:
    login.exibir_login(usuarios)
    st.stop() # Garante que nada abaixo execute sem login

# 4. Preparação do Menu e Sidebar
# Se chegou aqui, está autenticado
user_id = st.session_state.get('user_id')
user_info = usuarios.get(user_id)

if not user_info:
    st.error("Erro ao carregar perfil do usuário.")
    st.stop()

user_role = user_info.get('role', 'OPERACIONAL')
is_adm = user_role == "ADM"
permissoes = user_info.get('modulos', [])

# Montagem dinâmica das opções baseada no seu MAPA_MODULOS_MESTRE
menu_options = ["Home"]
for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
    if is_adm or id_modulo in permissoes:
        menu_options.append(label)

if is_adm: 
    menu_options.append("Central de Comando")

# Chama a sidebar e pega a escolha do usuário
escolha = config.desenhar_sidebar(user_info, menu_options)

# 5. Roteador Central
if escolha == "Home":
    home.exibir(user_info)

elif "Manutenção" in escolha:
    from modulos import mod_manutencao
    mod_manutencao.main()

elif "Minha Spin" in escolha:
    from modulos import mod_spin
    mod_spin.exibir_tamagotchi(user_info)

elif "RH Docs" in escolha or "Cartas" in escolha:
    from views import mod_cartas
    mod_cartas.exibir(user_role)

elif "Processos" in escolha:
    from views import mod_processos
    mod_processos.exibir(user_role=user_role)

elif "Central de Comando" in escolha:
    from views import central
    # Proteção contra o erro AttributeError caso a função não exista no DB
    try:
        departamentos = db.carregar_departamentos()
    except AttributeError:
        # Fallback caso a função ainda não tenha sido criada no seu database.py
        departamentos = ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA", "ADM"]
    
    central.exibir(is_adm) # Chama a função exibir da sua nova view de comando
