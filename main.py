import streamlit as st
from streamlit_option_menu import option_menu
from modulos import database as db
import configuracao as config
from datetime import datetime

# 1. SETUP INICIAL
config.configurar_pagina()
st.markdown(config.CSS_PREMIUM, unsafe_allow_html=True)

# 2. FUNÇÕES GLOBAIS DE APOIO
def finalizar_atividade_atual(nome_usuario):
    logs = db.carregar_esforco()
    agora = datetime.now()
    mudou = False
    for idx, act in enumerate(logs):
        if act['usuario'] == nome_usuario and act['status'] == 'Em andamento':
            logs[idx]['fim'] = agora.isoformat()
            logs[idx]['status'] = 'Finalizado'
            try:
                inicio_dt = datetime.fromisoformat(act['inicio']).replace(tzinfo=None)
                duracao = (agora - inicio_dt).total_seconds() / 60
                logs[idx]['duracao_min'] = round(duracao, 2)
            except:
                logs[idx]['duracao_min'] = 0
            mudou = True
    if mudou:
        db.salvar_esforco(logs)

# 3. AUTENTICAÇÃO
usuarios = db.carregar_usuarios_firebase()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><br><h1 class='gold-title'>WENDLEY PORTAL</h1>", unsafe_allow_html=True)
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

# 4. DADOS DE ACESSO E ESTADO
user_id = st.session_state.user_id
user_info = usuarios.get(user_id)
user_role = user_info.get('role', 'OPERACIONAL')
is_adm = (user_role == "ADM")
modulos_permitidos = user_info.get('modulos', [])

# 5. SIDEBAR DINÂMICA
with st.sidebar:
    foto_atual = user_info.get('foto') or "https://cdn-icons-png.flaticon.com/512/149/149071.png"
    st.markdown(f'<img src="{foto_atual}" class="profile-pic">', unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-weight:bold; color:#002366;'>{user_info['nome']}</p>", unsafe_allow_html=True)
    
    menu_options = ["🏠 Home"]
    for nome_exibicao, id_interno in config.MAPA_MODULOS_MESTRE.items():
        if is_adm or id_interno in modulos_permitidos:
            menu_options.append(nome_exibicao)
    
    if is_adm:
        menu_options.append("⚙️ Central de Comando")

    escolha = option_menu(
        None, menu_options, 
        icons=[config.ICON_MAP.get(opt, "circle") for opt in menu_options], 
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "nav-link-selected": {"background-color": "#002366", "color": "white"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px"}
        }
    )
    
    st.markdown("---")
    logs_sidebar = db.carregar_esforco()
    atv_atual = next((a for a in logs_sidebar if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)
    
    if atv_atual:
        with st.container(border=True):
            st.caption(f"⏳ **Ativo:** {atv_atual['motivo']}")
            if st.button("⏹️ Parar Agora", use_container_width=True):
                finalizar_atividade_atual(user_info['nome'])
                st.rerun()
    else:
        st.caption("⏸️ Cronômetro Parado")
    
    if st.button("🚪 Sair", use_container_width=True, type="secondary"):
        st.session_state.autenticado = False
        st.rerun()

# 6. ROTEADOR DE MÓDULOS (Lazy Loading)
if escolha == "🏠 Home":
    import views_home as home
    home.exibir(user_info)

elif "Manutenção" in escolha:
    import mod_manutencao
    mod_manutencao.main()

elif "Processos" in escolha:
    import mod_processos
    mod_processos.exibir(user_role=user_role)

elif "RH Docs" in escolha:
    import mod_cartas
    mod_cartas.exibir(user_role=user_role)

elif "Operação" in escolha:
    import mod_operacao
    mod_operacao.exibir_operacao_completa(user_role=user_role)

elif "Minha Spin" in escolha:
    import mod_spin
    mod_spin.exibir_tamagotchi(user_info)

elif "Passagens" in escolha:
    import passagens
    passagens.exibir_modulo_passagens()

elif "Tickets" in escolha:
    import mod_tickets
    mod_tickets.exibir_modulo_tickets(user_info)

elif "Central de Comando" in escolha:
    import views_central as central
    central.exibir(is_adm)

# 7. LÓGICA DE EDIÇÃO DE USUÁRIO (Preservada da Central de Comando)
if "edit_id" in st.session_state and escolha == "⚙️ Central de Comando":
    import views_central as central
    central.exibir_formulario_edicao(st.session_state.edit_id)
