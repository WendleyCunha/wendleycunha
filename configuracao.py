import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta
import pandas as pd

# --- 1. CONFIGURAÇÃO (Sempre o primeiro comando st) ---
def configurar_pagina():
    # Se der erro aqui, certifique-se que não há nenhum st.write antes desta linha
    if 'configurado' not in st.session_state:
        st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")
        st.session_state.configurado = True

# --- 2. CORES E CSS ---
COLOR_BG = "#FFFFFF"           # Branco
COLOR_SIDEBAR = "#1A1C22"      # Grafite
COLOR_GOLD = "#B8860B"         # Dourado
COLOR_TEXT = "#2D2E33"         # Cinza escuro

CSS_ESTAVEL = f"""
<style>
    .stApp {{ background-color: {COLOR_BG} !important; color: {COLOR_TEXT} !important; }}
    [data-testid="stSidebar"] {{ background-color: {COLOR_SIDEBAR} !important; }}
    h1, h2, h3, p, span, label {{ color: {COLOR_TEXT} !important; }}
    .profile-pic {{
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 3px solid {COLOR_GOLD};
        margin: 0 auto 10px auto; display: block;
    }}
    .sb-nome {{ color: white !important; text-align: center; font-weight: 600; margin-bottom: 0; }}
    .sb-cargo {{ color: {COLOR_GOLD} !important; text-align: center; font-size: 0.8rem; margin-top: 0; font-weight: bold; }}
    .stAlert {{ background-color: #F8F9FA !important; border: 1px solid #E9ECEF !important; color: {COLOR_TEXT} !important; }}
</style>
"""

# --- 3. DADOS INICIAIS ---
if 'atividades' not in st.session_state:
    st.session_state.atividades = [
        {"id": 1, "tarefa": "Ajuste de Fluxo Operacional", "data": datetime.now().date()},
        {"id": 2, "tarefa": "Checklist de Melhoria Contínua", "data": datetime.now().date() - timedelta(days=2)}
    ]

# --- 4. FUNÇÕES DO SEU CÓDIGO ORIGINAL ---
def desenhar_sidebar(user_info, menu_options):
    mapa_icones = {
        "Home": "house", "Manutenção": "tools", "Processos": "diagram-3",
        "RH Docs": "file-text", "Operação": "box", "Minha Spin": "car",
        "Cartas": "envelope", "Central de Comando": "shield-lock"
    }
    icones_dinamicos = [mapa_icones.get(opt, "circle") for opt in menu_options]

    with st.sidebar:
        foto = user_info.get('foto') or 'https://www.w3schools.com/howto/img_avatar.png'
        st.markdown(f'<img src="{foto}" class="profile-pic">', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-nome">{user_info.get("nome", "Usuário")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-cargo">{user_info.get("cargo", "Analista")}</p>', unsafe_allow_html=True)
        st.divider()

        escolha = option_menu(
            menu_title=None, 
            options=menu_options,
            icons=icones_dinamicos, 
            styles={
                "container": {"background-color": "transparent"},
                "nav-link": {"color": "#CCC", "font-size": "14px", "text-align": "left"},
                "nav-link-selected": {"background-color": COLOR_GOLD, "color": "white"}
            }
        )
        
        if st.button("Sair do Sistema"):
            st.session_state.autenticado = False
            st.rerun()
    return escolha

# --- 5. NOVA LÓGICA: CENTRAL DE COMANDO ---
def tela_central_comando():
    st.title("🛡️ Central de Comando")
    
    # Filtros de Data
    with st.expander("🔍 Filtros de Data", expanded=True):
        col1, col2 = st.columns([1, 2])
        tipo_filtro = col1.selectbox("Período", ["Hoje", "Últimos 7 dias", "Mês anterior", "Personalizado"])
        
        hoje = datetime.now().date()
        data_ini, data_fim = hoje, hoje

        if tipo_filtro == "Últimos 7 dias":
            data_ini = hoje - timedelta(days=7)
        elif tipo_filtro == "Mês anterior":
            data_fim = hoje.replace(day=1) - timedelta(days=1)
            data_ini = data_fim.replace(day=1)
        elif tipo_filtro == "Personalizado":
            periodo = col2.date_input("Selecione", [hoje, hoje])
            if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
                data_ini, data_fim = periodo

    aba_moni, aba_dash = st.tabs(["📊 Monitoramento", "📈 Dash"])

    # Filtragem
    df = pd.DataFrame(st.session_state.atividades)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data']).dt.date
        df_filtrado = df[(df['data'] >= data_ini) & (df['data'] <= data_fim)]
    else:
        df_filtrado = pd.DataFrame()

    with aba_moni:
        if df_filtrado.empty:
            st.info("Nada para mostrar neste período.")
        else:
            for _, row in df_filtrado.iterrows():
                c1, c2, c3 = st.columns([1, 3, 1])
                c1.write(f"ID #{row['id']}")
                c2.write(f"**{row['tarefa']}**")
                if c3.button("Encerrar", key=f"btn_{row['id']}"):
                    st.session_state.atividades = [a for a in st.session_state.atividades if a['id'] != row['id']]
                    st.rerun()
                st.divider()

    with aba_dash:
        if not df_filtrado.empty:
            st.metric("Atividades Ativas", len(df_filtrado))
            st.bar_chart(df_filtrado['data'].value_counts())

# --- 6. EXECUÇÃO DO APP ---
configurar_pagina()
st.markdown(CSS_ESTAVEL, unsafe_allow_html=True)

# Dados do Usuário (Simulado)
user_info = {"nome": "Wendley Leite Cunha", "cargo": "Melhoria Contínua Jr"}
menu_options = ["Home", "Central de Comando", "Processos", "Operação"]

escolha = desenhar_sidebar(user_info, menu_options)

if escolha == "Central de Comando":
    tela_central_comando()
else:
    st.subheader(f"Módulo {escolha}")
    st.write("Em desenvolvimento...")
