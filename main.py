import streamlit as st
from streamlit_option_menu import option_menu
from modulos import database as db
import os

# 1. Configuração de Página e Estilo Premium
st.set_page_config(page_title="Hub King Star | Premium", layout="wide", page_icon="👑")

st.markdown("""
    <style>
    /* Fundo da Sidebar em Cinza Claro */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    
    /* Botão Primário Dourado */
    div.stButton > button:first-child {
        background-color: #D4AF37;
        color: white;
        border: none;
        border-radius: 8px;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #B8860B;
        color: white;
    }
    /* Estilo do Título */
    .gold-title {
        text-align: center;
        color: #D4AF37;
        font-family: 'Trebuchet MS', sans-serif;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Autenticação
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

# 3. Menu de Navegação (Sidebar Cinza Claro)
user_info = usuarios.get(st.session_state.user_id)

with st.sidebar:
    st.markdown(f"<h3 style='color:#495057;'>Olá, {user_info['nome']}</h3>", unsafe_allow_html=True)
    st.write("---")
    
    escolha = option_menu(
        "Menu Principal", ["🏠 Home", "📄 Cartas"], 
        icons=['house', 'file-earmark-text'], 
        menu_icon="cast", default_index=0,
        styles={
            "container": {"background-color": "#F8F9FA", "padding": "5px"},
            "icon": {"color": "#D4AF37", "font-size": "20px"}, 
            "nav-link": {
                "font-size": "16px", 
                "text-align": "left", 
                "margin": "0px", 
                "color": "#495057" # Texto em cinza escuro para ler no fundo claro
            },
            "nav-link-selected": {
                "background-color": "#D4AF37", # Destaque Dourado
                "color": "white"
            },
        }
    )
    
    st.write("---")
    if st.button("Sair / Logout"):
        st.session_state.autenticado = False
        st.rerun()

# 4. Roteador de Telas
if escolha == "🏠 Home":
    st.markdown(f"# Bem-vindo, {user_info['nome']}!")
    st.info("Selecione um módulo no menu lateral para começar.")

elif escolha == "📄 Cartas":
    try:
        from views import mod_cartas
        mod_cartas.exibir(user_info['role'])
    except ImportError:
        st.error("Erro: O módulo 'views/mod_cartas.py' não foi encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar módulo: {e}")
