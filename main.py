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

# Injeção de CSS de Alta Prioridade - ELIMINANDO O FUNDO BRANCO/PRETO
st.markdown("""
    <style>
        /* 1. FORÇA O FUNDO DA SIDEBAR (AZUL AÇO CLARO) */
        section[data-testid="stSidebar"] {
            background-color: #4682B4 !important;
            background-image: linear-gradient(180deg, #4682B4 0%, #35638a 100%) !important;
        }

        /* 2. EXPLODE QUALQUER FUNDO BRANCO OU ESCURO INTERNO */
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] section,
        [data-testid="stSidebarNav"] {
            background-color: transparent !important;
        }

        /* 3. TEXTOS, ÍCONES E LABELS (BRANCO E DOURADO) */
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        /* Ícones especificamente em Dourado */
        [data-testid="stSidebar"] svg {
            fill: #FFD700 !important;
        }

        /* 4. BOTÕES E LINKS (DOURADO NO HOVER) */
        [data-testid="stSidebar"] button, 
        [data-testid="stSidebarNavItems"] a {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 10px !important;
            margin-bottom: 5px !important;
            transition: 0.3s;
        }

        [data-testid="stSidebar"] button:hover, 
        [data-testid="stSidebarNavItems"] a:hover {
            color: #FFD700 !important;
            background-color: rgba(255, 215, 0, 0.2) !important;
            border: 1px solid #FFD700 !important;
        }

        /* 5. DESTAQUE PARA O ITEM SELECIONADO */
        [data-testid="stSidebarNavItems"] a[aria-current="page"] {
            background-color: #B8860B !important; /* Dourado Escuro */
            color: white !important;
            font-weight: bold !important;
        }

        /* 6. CORREÇÃO PARA A FOTO DE PERFIL (Círculo Dourado) */
        [data-testid="stSidebar"] img {
            border: 3px solid #FFD700 !important;
            border-radius: 50% !important;
        }

        /* 7. REMOVE O HEADER DO STREAMLIT QUE PODE ESTAR PRETO */
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
    st.error("Erro: Não foi possível carregar a base de usuários do Firebase.")
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
    st.warning("⚠️ Perfil não identificado. Por favor, refaça o login.")
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
