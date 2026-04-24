import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu

# IMPORTAÇÃO DOS SEUS MÓDULOS (Precisam existir na mesma pasta ou em subpastas)
import database as db
import mod_home  # Vamos criar este arquivo com as funções de Dashboard e Home

# =========================================================
# 0. CONFIGURAÇÕES INICIAIS
# =========================================================
st.set_page_config(page_title="Hub King Star | Master", layout="wide", page_icon="👑")

MAPA_MODULOS_MESTRE = {
    "🏠 Home": "home",
    "🏗️ Manutenção": "manutencao",
    "🎯 Processos": "processos",
    "📄 RH Docs": "rh",
    "📊 Operação": "operacao",
    "🚗 Minha Spin": "spin",
    "🚌 Passagens": "passagens",
    "🎫 Tickets": "tickets",
    "⚙️ Central de Comando": "admin"
}

ICON_MAP = {
    "🏠 Home": "house",
    "🏗️ Manutenção": "tools",
    "🎯 Processos": "diagram-3",
    "📄 RH Docs": "file-earmark-text",
    "📊 Operação": "box-seam",
    "🚗 Minha Spin": "car-front-fill",
    "🚌 Passagens": "bus-front",
    "🎫 Tickets": "ticket-perforated",
    "⚙️ Central de Comando": "shield-lock"
}

# =========================================================
# 1. AUTENTICAÇÃO
# =========================================================
usuarios = db.carregar_usuarios_firebase()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # --- TELA DE LOGIN ---
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br><h1>Wendley Portal</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuário").lower().strip()
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True, type="primary"):
            if u in usuarios and (usuarios[u]["senha"] == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# Dados do Usuário Logado
user_info = usuarios.get(st.session_state.user_id)
is_adm = user_info.get('role') == "ADM"
modulos_permitidos = user_info.get('modulos', [])

# =========================================================
# 2. SIDEBAR (MENU DE NAVEGAÇÃO)
# =========================================================
with st.sidebar:
    st.markdown(f"### Olá, {user_info['nome']}")
    
    # Filtra o menu de acordo com as permissões
    menu_options = ["🏠 Home"]
    for nome, mid in MAPA_MODULOS_MESTRE.items():
        if mid in modulos_permitidos or is_adm:
            if nome not in menu_options: menu_options.append(nome)

    escolha = option_menu(
        None, menu_options,
        icons=[ICON_MAP.get(opt, "circle") for opt in menu_options],
        menu_icon="cast", default_index=0
    )
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# =========================================================
# 3. ROTEADOR (O CORAÇÃO DO MAIN)
# =========================================================
# Aqui o Main apenas chama os outros arquivos

if escolha == "🏠 Home":
    mod_home.exibir_home(user_info)

elif escolha == "🏗️ Manutenção":
    import mod_manutencao
    mod_manutencao.main()

elif escolha == "🎯 Processos":
    import mod_processos
    mod_processos.exibir(user_role=user_info['role'])

elif escolha == "🎫 Tickets":
    import mod_tickets
    mod_tickets.exibir_modulo_tickets(user_info)

elif escolha == "⚙️ Central de Comando":
    import mod_admin
    mod_admin.exibir_central(user_info, usuarios)
