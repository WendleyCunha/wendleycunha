import streamlit as st
from streamlit_option_menu import option_menu
from modulos import database as db

# 1. Configuração de Página e Estilo Premium
st.set_page_config(page_title="Hub King Star | Premium", layout="wide", page_icon="👑")

st.markdown("""
    <style>
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
            # Validação: Firebase ou Senha Mestra
            if u in usuarios and (usuarios[u]["senha"] == p or p == "master77"):
                st.session_state.autenticado = True
                st.session_state.user_id = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# 3. Menu de Navegação (Views)
user_info = usuarios.get(st.session_state.user_id)
is_adm = user_info.get('role') == "ADM"
modulos_permitidos = user_info.get('modulos', [])

with st.sidebar:
    st.markdown(f"<h2 style='color:#D4AF37;'>Olá, {user_info['nome']}</h2>", unsafe_allow_html=True)
    
    # Define quais módulos aparecem no menu
    menu_map = {"🏠 Home": "home", "📄 Cartas": "cartas"} # Adicione os outros aqui
    
    escolha = option_menu(
        "Menu Principal", ["🏠 Home", "📄 Cartas"], 
        icons=['house', 'file-earmark-text'], 
        menu_icon="cast", default_index=0,
        styles={
            "container": {"background-color": "#0E1117"},
            "icon": {"color": "#D4AF37", "font-size": "20px"}, 
            "nav-link-selected": {"background-color": "#D4AF37"},
        }
    )

# 4. Roteador de Telas
if escolha == "🏠 Home":
    st.write("Bem-vindo ao Dashboard!")
elif escolha == "📄 Cartas":
    from views import mod_cartas
    mod_cartas.exibir(user_info['role'])
