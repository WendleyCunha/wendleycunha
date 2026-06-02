import streamlit as st
import configuracao as config
from modulos import database as db
from views import home, login
from datetime import datetime
from pwa_inject import injetar_pwa

# --- 1. CACHE DE USUÁRIOS ---
@st.cache_data(ttl=600)
def obter_usuarios_cache():
    try:
        return db.carregar_usuarios_firebase()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
        return {}

# --- 2. CONFIGURAÇÃO INICIAL ---
config.configurar_pagina()
injetar_pwa()

# ══════════════════════════════════════════════════════════════════
#  CSS GLOBAL — Identidade Visual Azul Marinho + Dourado
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Reset e Base ─────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: #f0f4f8 !important;
}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #0d2145 40%, #102a57 100%) !important;
    border-right: 1px solid rgba(255,215,0,0.15) !important;
    min-width: 260px !important;
}
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebarNav"] {
    background: transparent !important;
}

/* Textos da sidebar */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown {
    color: #c8d8f0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
[data-testid="stSidebar"] svg { fill: #FFD700 !important; }

/* Itens de navegação */
[data-testid="stSidebarNavItems"] a {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
    margin: 3px 8px !important;
    border: 1px solid rgba(255,215,0,0.08) !important;
    transition: all 0.25s ease !important;
    padding: 10px 14px !important;
}
[data-testid="stSidebarNavItems"] a:hover {
    background: rgba(255,215,0,0.1) !important;
    border-color: rgba(255,215,0,0.3) !important;
}
[data-testid="stSidebarNavItems"] a[aria-current="page"] {
    background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,165,0,0.15)) !important;
    border: 1px solid #FFD700 !important;
    font-weight: 700 !important;
}

/* ── Header transparente ──────────────────────────────── */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

/* ── Área principal ───────────────────────────────────── */
[data-testid="stMain"] {
    background: #f0f4f8 !important;
}
.block-container {
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Títulos e headings ───────────────────────────────── */
h1 { 
    font-size: 1.75rem !important; 
    font-weight: 800 !important; 
    color: #0a1628 !important;
    letter-spacing: -0.02em !important;
}
h2, h3 { 
    font-weight: 700 !important; 
    color: #0d2145 !important;
    letter-spacing: -0.01em !important;
}

/* ── Abas (Tabs) ──────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #ffffff !important;
    border-radius: 12px !important;
    padding: 6px !important;
    gap: 4px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 9px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    color: #64748b !important;
    background: transparent !important;
    border: none !important;
    transition: all 0.2s ease !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background: #f1f5f9 !important;
    color: #0d2145 !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: linear-gradient(135deg, #0d2145, #1a3a6e) !important;
    color: #FFD700 !important;
    box-shadow: 0 2px 8px rgba(13,33,69,0.3) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    display: none !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Botões ───────────────────────────────────────────── */
.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.2rem !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0d2145, #1a3a6e) !important;
    color: #FFD700 !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(13,33,69,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1a3a6e, #234d8a) !important;
    box-shadow: 0 5px 15px rgba(13,33,69,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: #fff !important;
    color: #0d2145 !important;
    border: 1.5px solid #c7d2fe !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #0d2145 !important;
    background: #f8faff !important;
}

/* ── Inputs ───────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #0d2145 !important;
    box-shadow: 0 0 0 3px rgba(13,33,69,0.1) !important;
}

/* ── Dataframe ────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
}

/* ── Alertas e Info boxes ─────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── Métricas ─────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #fff !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    border: 1px solid #e2e8f0 !important;
}
[data-testid="stMetricValue"] {
    color: #0a1628 !important;
    font-weight: 800 !important;
}

/* ── Containers com borda ─────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 14px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}

/* ── Expander ─────────────────────────────────────────── */
[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    background: #fff !important;
}

/* ── Segmented control ────────────────────────────────── */
[data-testid="stSegmentedControl"] {
    background: #fff !important;
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    padding: 4px !important;
}

/* ── Divider ──────────────────────────────────────────── */
hr {
    border-color: #e2e8f0 !important;
}

/* ── Scrollbar personalizada ──────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f0f4f8; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* ── Sidebar logo/header ──────────────────────────────── */
.sidebar-logo {
    padding: 20px 16px 16px;
    border-bottom: 1px solid rgba(255,215,0,0.15);
    margin-bottom: 12px;
}
.sidebar-user-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,215,0,0.15);
    border-radius: 12px;
    padding: 12px 14px;
    margin: 0 8px 16px;
}
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
for key, default in {
    "autenticado": False,
    "user_info": None,
    "user_id": None,
    "pagina_atual": "Home"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- 4. USUÁRIOS ---
usuarios = obter_usuarios_cache()

# --- 5. LOGIN ---
if not st.session_state.autenticado:
    if not usuarios:
        st.error("Sistema offline. Verifique a conexão com Firebase.")
        st.stop()
    login.exibir_login(usuarios)
    st.stop()

# --- 6. PERFIL ---
user_id   = st.session_state.user_id
user_info = st.session_state.user_info

if not user_info and user_id in usuarios:
    user_info = usuarios.get(user_id)
    st.session_state.user_info = user_info

if not user_info:
    st.warning("⚠️ Perfil não identificado. Por favor, refaça o login.")
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()
    st.stop()

user_role  = user_info.get('role', 'OPERACIONAL')
is_adm     = (user_role == "ADM")
permissoes = user_info.get('modulos', [])

# --- 7. SIDEBAR VISUAL ---
with st.sidebar:
    # Logo / Brand
    st.markdown("""
        <div class="sidebar-logo">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:38px;height:38px;background:linear-gradient(135deg,#FFD700,#FFA500);
                            border-radius:10px;display:flex;align-items:center;justify-content:center;
                            font-size:18px;font-weight:900;color:#0a1628;flex-shrink:0;">
                    ✦
                </div>
                <div>
                    <div style="color:#ffffff;font-size:14px;font-weight:800;
                                font-family:'Plus Jakarta Sans',sans-serif;letter-spacing:-0.01em;">
                        PORTAL GESTÃO
                    </div>
                    <div style="color:#FFD700;font-size:10px;font-weight:600;
                                letter-spacing:0.1em;text-transform:uppercase;">
                        Sistema Integrado
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # User card
    role_color = "#FFD700" if is_adm else "#7dd3fc"
    role_label = "Administrador" if is_adm else user_role.title()
    st.markdown(f"""
        <div class="sidebar-user-card">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;background:linear-gradient(135deg,#FFD700,#FFA500);
                            border-radius:50%;display:flex;align-items:center;justify-content:center;
                            font-weight:800;color:#0a1628;font-size:14px;flex-shrink:0;">
                    {user_info['nome'][0].upper()}
                </div>
                <div>
                    <div style="color:#ffffff;font-size:13px;font-weight:700;
                                font-family:'Plus Jakarta Sans',sans-serif;">
                        {user_info['nome'].split()[0]}
                    </div>
                    <div style="color:{role_color};font-size:10px;font-weight:600;
                                letter-spacing:0.06em;text-transform:uppercase;">
                        {role_label}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Navegação
    menu_options = ["🏠 Home"]
    for label, id_modulo in getattr(config, 'MAPA_MODULOS_MESTRE', {}).items():
        if is_adm or id_modulo in permissoes:
            menu_options.append(label)
    if is_adm:
        menu_options.append("⚙️ Central de Comando")

    st.markdown("""
        <div style="color:rgba(200,216,240,0.5);font-size:10px;font-weight:700;
                    letter-spacing:0.12em;text-transform:uppercase;
                    padding:8px 16px 6px;margin-top:4px;">
            NAVEGAÇÃO
        </div>
    """, unsafe_allow_html=True)

    escolha = st.radio(
        "menu",
        menu_options,
        label_visibility="collapsed",
        key="nav_radio"
    )

    # Rodapé da sidebar
    st.markdown("""
        <div style="position:fixed;bottom:16px;left:0;width:260px;
                    padding:0 16px;pointer-events:none;">
            <div style="border-top:1px solid rgba(255,215,0,0.12);
                        padding-top:12px;text-align:center;">
                <div style="color:rgba(200,216,240,0.35);font-size:10px;
                            font-family:'Plus Jakarta Sans',sans-serif;">
                    v2.0 · Portal de Gestão
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 8. ROTEADOR ---
try:
    if "Home" in escolha:
        home.exibir(user_info)

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
        central.exibir(is_adm)

except Exception as e:
    st.error(f"Ocorreu um erro ao carregar o módulo: {escolha}")
    st.info("Tente atualizar a página ou contatar o administrador.")
    print(f"DEBUG: Erro no módulo {escolha}: {e}")
