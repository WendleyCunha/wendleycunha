import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login

# --- 1. FUNÇÃO DE CACHE ---
@st.cache_data(ttl=600)  # Mantém os dados na memória por 10 minutos
def obter_usuarios_cache():
    """Busca usuários no Firebase apenas uma vez a cada 10 minutos."""
    try:
        return db.carregar_usuarios_firebase()
    except Exception:
        return {}

# --- 2. CONFIGURAÇÃO INICIAL E ESTILO ---
config.configurar_pagina()

# Injeção de CSS Refinado - ELIMINAÇÃO TOTAL DO PRETO
st.markdown("""
    <style>
        /* 1. FUNDO DA BARRA LATERAL (GRADIENTE AZUL) */
        [data-testid="stSidebar"] {
            background-color: #4682B4 !important;
            background-image: linear-gradient(180deg, #002366 0%, #001a4d 100%) !important;
        }

        /* 2. REMOVE FUNDO PRETO DO CONTAINER DE NAVEGAÇÃO NATIVO */
        [data-testid="stSidebarNav"], 
        [data-testid="stSidebarNav"] ul {
            background-color: transparent !important;
        }
        
        /* 3. TEXTOS E LABELS EM BRANCO PARA CONTRASTE */
        [data-testid="stSidebar"] .stText, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebarNavItems"] a {
            color: #FFFFFF !important;
            text-decoration: none !important;
        }

        /* 4. ESTILIZAÇÃO DOS ÍCONES (DOURADO) */
        [data-testid="stSidebar"] svg {
            fill: #FFD700 !important;
        }

        /* 5. EFEITO HOVER E ITEM SELECIONADO (DOURADO) */
        /* Garante que o item ativo ou focado brilhe em dourado */
        [data-testid="stSidebarNavItems"] a:hover,
        [data-testid="stSidebarNavItems"] a[aria-current="page"] {
            color: #FFD700 !important;
            background-color: rgba(255, 215, 0, 0.15) !important;
            border-left: 4px solid #FFD700 !important;
        }

        /* 6. ESTILIZAÇÃO DE BOTÕES (CASO EXISTA NA SIDEBAR) */
        [data-testid="stSidebar"] button {
            color: #FFFFFF !important;
            background-color: transparent !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] button:hover {
            color: #FFD700 !important;
            border: 1px solid #FFD700 !important;
            background-color: rgba(255, 215, 0, 0.1) !important;
        }

        /* 7. AJUSTE DE SELECTBOX (AZUL ESCURO COM BORDA DOURADA) */
        div[data-baseweb="select"] > div {
            background-color: #001a4d !important;
            border-color: #FFD700 !important;
            color: white !important;
        }
        
        /* 8. ELIMINA LINHA DIVISORA CINZA */
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
    st.info("Isso pode ser limite de cota atingido ou erro de conexão.")
    st.stop()

# --- 5. LÓGICA DE LOGIN ---
if not st.session_state.autenticado:
    login.exibir_login(usuarios)
    st.stop() 

# --- 6. RECUPERAÇÃO SEGURA DO PERFIL ---
user_id = st.session_state.get('user_id')
user_info = st.session_state.get('user_info')

# Recuperação em caso de refresh (F5)
if not user_info and user_id and usuarios:
    user_info = usuarios.get(user_id)
    st.session_state.user_info = user_info

# Blindagem contra quedas de sessão inesperadas
if user_info is None:
    st.warning("⚠️ Perfil não identificado. Por favor, refaça o login.")
    if st.button("Ir para Login"):
        st.session_state.autenticado = False
        st.rerun()
    st.stop()

# Definições de permissão para uso no roteamento
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

# Chamada da sidebar (definida em configuracao.py)
escolha = config.desenhar_sidebar(user_info, menu_options)

# --- 8. ROTEADOR CENTRAL (LOADER DE VIEWS) ---
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
    st.info("Verifique a conexão ou a estrutura do módulo.")
    print(f"Erro detalhado no console: {e}")
