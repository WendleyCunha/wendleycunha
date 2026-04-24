import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login

# 1. Configuração Inicial (Força as cores corretas antes de tudo)
config.configurar_pagina()

# 2. Inicialização Robusta do Session State
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# 3. Carregamento de Dados de Usuários (com tratamento de erro)
try:
    usuarios = db.carregar_usuarios_firebase()
except Exception:
    usuarios = {}
    st.error("Erro de conexão com o banco de dados.")

# 4. Lógica de Login
if not st.session_state.autenticado:
    login.exibir_login(usuarios)
    st.stop() 

# 5. Recuperação Segura do Perfil (Evita quedas por perda de cache)
user_id = st.session_state.get('user_id')
user_info = st.session_state.get('user_info')

# Se perdemos o user_info mas temos o id, tentamos recuperar do banco
if not user_info and user_id and usuarios:
    user_info = usuarios.get(user_id)
    st.session_state.user_info = user_info

# --- BLINDAGEM FINAL CONTRA QUEDAS ---
if user_info is None:
    st.warning("⚠️ Perfil não identificado. Por favor, refaça o login.")
    if st.button("Ir para Login"):
        st.session_state.autenticado = False
        st.rerun()
    st.stop()

# Garantia de dados mínimos para evitar erros nos módulos
user_role = user_info.get('role', 'OPERACIONAL')
is_adm = (user_role == "ADM")
permissoes = user_info.get('modulos', [])

# 6. Montagem dinâmica do Menu
menu_options = ["Home"]
for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
    # Se for ADM ou tiver a permissão específica, adiciona ao menu
    if is_adm or id_modulo in permissoes:
        menu_options.append(label)

if is_adm: 
    menu_options.append("Central de Comando")

# Sidebar (Chama a função que limpa as cores)
escolha = config.desenhar_sidebar(user_info, menu_options)

# 7. Roteador Central com Proteção contra erros de importação
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
        except Exception:
            departamentos = ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA", "ADM"]
        
        central.exibir(is_adm)

except Exception as e:
    st.error(f"Erro ao carregar o módulo '{escolha}'.")
    st.info("Dica: Verifique se todos os arquivos estão atualizados no GitHub.")
    print(f"Erro detalhado no roteador: {e}")
