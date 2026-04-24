import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login

# --- 1. FUNÇÃO DE CACHE (A CHAVE PARA ECONOMIZAR LEITURAS) ---
@st.cache_data(ttl=600)  # Mantém os dados na memória por 600 segundos (10 minutos)
def obter_usuarios_cache():
    """Busca usuários no Firebase apenas uma vez a cada 10 minutos."""
    try:
        return db.carregar_usuarios_firebase()
    except Exception:
        return {}

# 2. Configuração Inicial
config.configurar_pagina()

# 3. Inicialização do Session State
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# 4. Carregamento Inteligente (Usa o cache em vez de ir direto ao banco)
usuarios = obter_usuarios_cache()

if not usuarios and not st.session_state.autenticado:
    st.error("Erro: Não foi possível carregar a base de usuários do Firebase.")
    st.info("Isso pode ser limite de cota atingido ou erro de conexão.")
    st.stop()

# 5. Lógica de Login
if not st.session_state.autenticado:
    login.exibir_login(usuarios)
    st.stop() 

# 6. Recuperação Segura do Perfil
user_id = st.session_state.get('user_id')
user_info = st.session_state.get('user_info')

# Se perdemos o user_info (refresh da página), recuperamos do cache local
if not user_info and user_id and usuarios:
    user_info = usuarios.get(user_id)
    st.session_state.user_info = user_info

# Blindagem contra quedas de sessão
if user_info is None:
    st.warning("⚠️ Perfil não identificado. Por favor, refaça o login.")
    if st.button("Ir para Login"):
        st.session_state.autenticado = False
        st.rerun()
    st.stop()

# Definições de permissão
user_role = user_info.get('role', 'OPERACIONAL')
is_adm = (user_role == "ADM")
permissoes = user_info.get('modulos', [])

# 7. Montagem dinâmica do Menu
menu_options = ["Home"]
for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
    if is_adm or id_modulo in permissoes:
        menu_options.append(label)

if is_adm: 
    menu_options.append("Central de Comando")

# Sidebar
escolha = config.desenhar_sidebar(user_info, menu_options)

# 8. Roteador Central
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
        # Busca departamentos (Ideal também colocar cache aqui depois)
        try:
            departamentos = db.carregar_departamentos()
        except Exception:
            departamentos = ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA", "ADM"]
        
        central.exibir(is_adm)

except Exception as e:
    st.error(f"Erro ao carregar o módulo '{escolha}'.")
    st.info("Verifique a conexão ou se houve estouro de cota do Firebase.")
    print(f"Erro detalhado: {e}")
