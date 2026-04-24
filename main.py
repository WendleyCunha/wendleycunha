import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login

# 1. Configuração Inicial (Título, Layout, etc.)
config.configurar_pagina()

# 2. Inicialização do Session State
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# 3. Carregamento de Dados de Usuários
usuarios = db.carregar_usuarios_firebase()

# 4. Lógica de Login
if not st.session_state.autenticado:
    login.exibir_login(usuarios)
    st.stop() 

# 5. Recuperação Segura do Perfil
# Buscamos primeiro no session_state para evitar depender do Firebase em cada clique
user_info = st.session_state.get('user_info')

# Se não estiver no session_state, tentamos buscar pelo ID salvo
if not user_info:
    user_id = st.session_state.get('user_id')
    user_info = usuarios.get(user_id)
    # Salva no estado para a próxima interação ser mais rápida
    st.session_state.user_info = user_info

# --- BLINDAGEM CONTRA ATTRIBUTEERROR ---
if user_info is None:
    st.error("⚠️ Sessão expirada ou perfil não encontrado.")
    if st.button("Reiniciar Sistema"):
        st.session_state.autenticado = False
        st.rerun()
    st.stop()

# Agora o .get() nunca falhará pois garantimos que user_info existe
user_role = user_info.get('role', 'OPERACIONAL')
is_adm = (user_role == "ADM")
permissoes = user_info.get('modulos', [])

# 6. Montagem dinâmica do Menu
menu_options = ["Home"]
for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
    if is_adm or id_modulo in permissoes:
        menu_options.append(label)

if is_adm: 
    menu_options.append("Central de Comando")

# Sidebar
escolha = config.desenhar_sidebar(user_info, menu_options)

# 7. Roteador Central (Execução dos Módulos)
try:
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
        try:
            departamentos = db.carregar_departamentos()
        except AttributeError:
            departamentos = ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA", "ADM"]
        
        central.exibir(is_adm)

except Exception as e:
    st.warning(f"Ocorreu um problema ao carregar o módulo {escolha}. Tente novamente.")
    # Log silencioso para você saber o que houve sem travar o app para o usuário
    print(f"Erro no roteador: {e}")
