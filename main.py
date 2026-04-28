import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login

# --- 1. FUNÇÃO DE CACHE ---
@st.cache_data(ttl=600)
def obter_usuarios_cache():
    try:
        return db.carregar_usuarios_firebase()
    except Exception:
        return {}

# --- 2. CONFIGURAÇÃO INICIAL E ESTILO ---
config.configurar_pagina()

# CSS de Alta Prioridade para Harmonia Total
st.markdown("""
    <style>
        /* 1. FUNDO DA SIDEBAR (AZUL AÇO) */
        [data-testid="stSidebar"] {
            background-color: #4682B4 !important;
            background-image: linear-gradient(180deg, #4682B4 0%, #2c5270 100%) !important;
        }

        /* 2. ELIMINAÇÃO DO RETÂNGULO BRANCO (FORÇA TRANSPARÊNCIA EM TODOS OS NÍVEIS) */
        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"],
        [data-testid="stSidebarNav"] {
            background-color: transparent !important;
        }

        /* 3. TEXTO E ÍCONES (BRANCO E DOURADO) */
        [data-testid="stSidebar"] .stText, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #FFFFFF !important;
        }

        /* Prioridade Dourada para Ícones */
        [data-testid="stSidebar"] svg {
            fill: #FFD700 !important;
        }

        /* 4. ESTILIZAÇÃO DO MENU (REMOVENDO O ASPECTO DE BLOCO) */
        [data-testid="stSidebarNavItems"] a {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
            margin: 4px 0px !important;
            border: 1px solid rgba(255, 215, 0, 0.1) !important;
            transition: all 0.3s ease;
        }

        /* 5. ITEM SELECIONADO - DOURADO PRIORIDADE 0 */
        [data-testid="stSidebarNavItems"] a[aria-current="page"] {
            background-color: #B8860B !important; /* Dourado Sólido */
            color: #FFFFFF !important;
            border: 1px solid #FFD700 !important;
            font-weight: bold !important;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
        }

        /* Hover - Brilho Dourado */
        [data-testid="stSidebarNavItems"] a:hover {
            color: #FFD700 !important;
            background-color: rgba(255, 215, 0, 0.15) !important;
            border: 1px solid #FFD700 !important;
        }

        /* 6. BOTÃO SAIR (MAIS DISCRETO) */
        [data-testid="stSidebar"] button {
            background-color: rgba(0, 0, 0, 0.2) !important;
            color: #FFD700 !important;
            border: 1px solid #FFD700 !important;
            border-radius: 5px !important;
        }

        /* 7. REMOVE O HEADER SUPERIOR */
        header[data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DO SESSION STATE ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# --- 4. CARREGAMENTO INTELIGENTE DE USUÁRIOS ---
usuarios = obter_usuarios_cache()

if not usuarios and not st.session_state.autenticado:
    st.error("Erro: Não foi possível carregar a base de usuários.")
    st.stop()

# --- 5. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    login.exibir_login(usuarios)
    st.stop() 

# --- 6. RECUPERAÇÃO SEGURA DO PERFIL ---
user_id = st.session_state.get('user_id')
user_info = st.session_state.get('user_info')

if not user_info and user_id and usuarios:
    user_info = usuarios.get(user_id)
    st.session_state.user_info = user_info

if user_info is None:
    st.warning("⚠️ Perfil não identificado.")
    if st.button("Ir para Login"):
        st.session_state.autenticado = False
        st.rerun()
    st.stop()

user_role = user_info.get('role', 'OPERACIONAL')
is_adm = (user_role == "ADM")
permissoes = user_info.get('modulos', [])

# --- 7. MONTAGEM DINÂMICA DO MENU ---
menu_options = ["Home"]
for label, id_modulo in config.MAPA_MODULOS_MESTRE.items():
    if is_adm or id_modulo in permissoes:
        menu_options.append(label)

if is_adm: 
    menu_options.append("Central de Comando")

# Chamada da sidebar
escolha = config.desenhar_sidebar(user_info, menu_options)

# --- 8. ROTEADOR CENTRAL ---
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
    print(f"Erro detalhado: {e}")
