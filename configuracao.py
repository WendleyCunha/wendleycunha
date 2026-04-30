import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA (Sempre o primeiro comando) ---
st.set_page_config(page_title="Hub King Star", layout="wide", page_icon="👑")

# --- CONSTANTES E CORES EXECUTIVAS KING STAR ---
COLOR_BG = "#FFFFFF"           # Branco (Fundo principal)
COLOR_SIDEBAR = "#1A1C22"      # Grafite (Sidebar)
COLOR_GOLD = "#B8860B"         # Dourado
COLOR_TEXT = "#2D2E33"         # Cinza escuro (Texto)

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
st.markdown(CSS_ESTAVEL, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO ESTADO (Para não perder dados) ---
if 'atividades' not in st.session_state:
    # Exemplo de dados iniciais
    st.session_state.atividades = [
        {"id": 101, "tarefa": "Manutenção Preventiva Spin", "data": datetime.now().date(), "status": "Em Execução"},
        {"id": 102, "tarefa": "Revisão Processo Logístico", "data": datetime.now().date() - timedelta(days=2), "status": "Em Execução"},
        {"id": 103, "tarefa": "Checklist Qualidade", "data": datetime.now().date() - timedelta(days=8), "status": "Em Execução"}
    ]

# --- FUNÇÕES DE INTERFACE ---
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
        st.markdown(f'<p class="sb-nome">{user_info.get("nome", "Wendley")}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sb-cargo">{user_info.get("cargo", "Analista de Melhoria Contínua Jr.")}</p>', unsafe_allow_html=True)
        st.divider()
        
        escolha = option_menu(
            menu_title=None, options=menu_options, icons=icones_dinamicos, 
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

def tela_central_comando():
    st.title("🛡️ Central de Comando")
    
    # --- FILTRO DE DATA ---
    with st.expander("🔍 Filtros de Data", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            tipo_filtro = st.selectbox(
                "Período de visualização",
                ["Hoje", "Últimos 7 dias", "Mês anterior", "Personalizado"]
            )
        
        hoje = datetime.now().date()
        data_ini, data_fim = hoje, hoje

        if tipo_filtro == "Últimos 7 dias":
            data_ini = hoje - timedelta(days=7)
        elif tipo_filtro == "Mês anterior":
            primeiro_dia_mes_atual = hoje.replace(day=1)
            data_fim = primeiro_dia_mes_atual - timedelta(days=1)
            data_ini = data_fim.replace(day=1)
        elif tipo_filtro == "Personalizado":
            with col2:
                periodo = st.date_input("Intervalo", [hoje, hoje])
                if isinstance(periodo, list) and len(periodo) == 2:
                    data_ini, data_fim = periodo

    # --- ABAS ---
    aba_monitoramento, aba_dash = st.tabs(["📊 Monitoramento", "📈 Dash"])

    # Filtragem dos dados para ambas as abas
    df_atividades = pd.DataFrame(st.session_state.atividades)
    if not df_atividades.empty:
        df_filtrado = df_atividades[
            (df_atividades['data'] >= data_ini) & 
            (df_atividades['data'] <= data_fim)
        ]
    else:
        df_filtrado = pd.DataFrame()

    with aba_monitoramento:
        st.subheader("Atividades em Tempo Real")
        if df_filtrado.empty:
            st.warning("Nenhuma atividade encontrada para este período.")
        else:
            for idx, row in df_filtrado.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([0.5, 3, 1])
                    c1.markdown(f"**ID:** {row['id']}")
                    c2.markdown(f"**Tarefa:** {row['tarefa']} \n\n *Início: {row['data'].strftime('%d/%m/%Y')}*")
                    # Botão individual de encerramento
                    if c3.button("Finalizar", key=f"encerrar_{row['id']}"):
                        # Remove da lista original usando o ID como referência
                        st.session_state.atividades = [a for a in st.session_state.atividades if a['id'] != row['id']]
                        st.toast(f"Atividade {row['id']} encerrada com sucesso!")
                        st.rerun()
                    st.divider()

    with aba_dash:
        st.subheader("Indicadores do Período")
        if df_filtrado.empty:
            st.info("Sem dados para gerar gráficos.")
        else:
            metrica1, metrica2 = st.columns(2)
            metrica1.metric("Total de Atividades", len(df_filtrado))
            metrica2.metric("Período Dias", (data_fim - data_ini).days + 1)
            
            # Exemplo de gráfico simples
            st.bar_chart(df_filtrado['data'].value_counts())
            st.dataframe(df_filtrado, use_container_width=True)

# --- EXECUÇÃO PRINCIPAL ---
user_info = {
    "nome": "Wendley Leite Cunha", 
    "cargo": "Analista de Melhoria Contínua Jr.",
    "foto": None
}
menu_options = ["Home", "Manutenção", "Processos", "Operação", "Central de Comando"]

escolha = desenhar_sidebar(user_info, menu_options)

if escolha == "Central de Comando":
    tela_central_comando()
else:
    st.title(f"Módulo: {escolha}")
    st.write("Conteúdo em desenvolvimento...")
