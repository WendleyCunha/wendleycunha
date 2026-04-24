import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login # Importa o novo arquivo de login

# 1. Configuração Inicial
config.configurar_pagina()

# 2. Carregamento de Dados e Estado
usuarios = db.carregar_usuarios_firebase()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# 3. Lógica de Login (Agora modularizada)
if not st.session_state.autenticado:
    login.exibir_login(usuarios)

# 4. Preparação do Menu e Sidebar
user_info = usuarios.get(st.session_state.user_id)
user_role = user_info.get('role', 'USER')
is_adm = user_role == "ADM"
permissoes = user_info.get('modulos', [])

# Montagem das opções
menu_options = ["Home"]
for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
    if is_adm or id_modulo in permissoes:
        menu_options.append(label)
if is_adm: menu_options.append("Central de Comando")

# Chama a sidebar e pega a escolha
escolha = config.desenhar_sidebar(user_info, menu_options)

# 5. Roteador Central (Apenas executa as views)
if escolha == "Home":
    home.exibir(user_info)

elif escolha == "Manutenção":
    from modulos import mod_manutencao
    mod_manutencao.main()

elif escolha == "Minha Spin":
    from modulos import mod_spin
    mod_spin.exibir_tamagotchi(user_info)

elif escolha == "Cartas":
    from views import mod_cartas
    mod_cartas.exibir(user_role)

elif escolha == "Central de Comando":
    from views import central
    departamentos = db.carregar_departamentos()
    central.exibir(usuarios, departamentos)
