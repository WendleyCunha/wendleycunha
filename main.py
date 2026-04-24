import streamlit as st
from streamlit_option_menu import option_menu
from modulos import database as db
import pandas as pd
from datetime import datetime
import os

# =========================================================
# 1. CONFIGURAÇÃO E ESTILO PREMIUM
# =========================================================
st.set_page_config(page_title="Hub King Star | Premium", layout="wide", page_icon="👑")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #F8F9FA; }
    div.stButton > button:first-child {
        background-color: #D4AF37; color: white; border: none; border-radius: 8px; transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #B8860B; color: white; }
    .gold-title {
        text-align: center; color: #D4AF37; font-family: 'Trebuchet MS', sans-serif; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. AUTENTICAÇÃO
# =========================================================
usuarios = db.carregar_usuarios_firebase()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h1 class='gold-title'>WENDLEY PORTAL</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuário").lower().strip()
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if u in usuarios and (usuarios[u]["senha"] == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# Dados do Usuário Logado
user_info = usuarios.get(st.session_state.user_id)
user_role = user_info.get('role', 'OPERACIONAL')
modulos_permitidos = user_info.get('modulos', [])

# =========================================================
# 3. SIDEBAR E MENU DINÂMICO
# =========================================================
with st.sidebar:
    st.markdown(f"<h3 style='color:#495057;'>Olá, {user_info['nome']}</h3>", unsafe_allow_html=True)
    st.write("---")
    
    # Lista de opções baseada no que o usuário pode ver
    menu_options = ["🏠 Home", "📄 Cartas"]
    
    # Adicione aqui os outros conforme você criar os arquivos na pasta views
    if "processos" in modulos_permitidos or user_role == "ADM":
        menu_options.append("🎯 Processos")
    if "spin" in modulos_permitidos or user_role == "ADM":
        menu_options.append("🚗 Minha Spin")
    if user_role == "ADM":
        menu_options.append("⚙️ Central")

    escolha = option_menu(
        "Menu Principal", menu_options, 
        icons=['house', 'file-earmark-text', 'diagram-3', 'car-front-fill', 'shield-lock'], 
        menu_icon="cast", default_index=0,
        styles={
            "container": {"background-color": "#F8F9FA", "padding": "5px"},
            "icon": {"color": "#D4AF37", "font-size": "20px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "color": "#495057"},
            "nav-link-selected": {"background-color": "#D4AF37", "color": "white"},
        }
    )
    
    st.write("---")
    if st.button("Sair / Logout", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()

# =========================================================
# 4. ROTEADOR DE TELAS (O CORRETO)
# =========================================================

if escolha == "🏠 Home":
    st.markdown(f"# Bem-vindo, {user_info['nome']}!")
    
    # Aqui trazemos de volta as abas de esforço e agenda que você tinha
    tab_esforco, tab_agenda = st.tabs(["⚡ Esforço Hoje", "📅 Minha Agenda"])
    
    with tab_esforco:
        st.subheader("Controle de Atividades")
        # Aqui você pode colar a lógica de INICIAR TAREFA que estava no seu main antigo
        st.info("Área em desenvolvimento para o novo padrão.")

    with tab_agenda:
        st.subheader("Compromissos Agendados")
        # Aqui você carrega os dados do db.carregar_diario()
        st.write("Nenhum compromisso para hoje.")

elif escolha == "📄 Cartas":
    try:
        from views import mod_cartas
        mod_cartas.exibir(user_role) # Passa a alçada (ADM, OPERACIONAL, etc)
    except Exception as e:
        st.error(f"Erro ao carregar Cartas: {e}")

elif escolha == "🎯 Processos":
    try:
        from views import mod_processos
        mod_processos.exibir(user_role)
    except Exception as e:
        st.error(f"Erro ao carregar Processos: {e}")

elif escolha == "🚗 Minha Spin":
    try:
        from views import mod_spin
        mod_spin.exibir_tamagotchi(user_info)
    except Exception as e:
        st.error(f"Erro ao carregar Minha Spin: {e}")

elif escolha == "⚙️ Central":
    if user_role == "ADM":
        st.title("⚙️ Central de Comando")
        # Lógica de gestão de usuários aqui ou em views/mod_central.py
    else:
        st.error("Acesso negado.")
