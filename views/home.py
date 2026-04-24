# views/home.py
import streamlit as st
import database as db # ou from modulos import database as db, conforme seu projeto

def exibir(user_info):
    st.title(f"Olá, {user_info['nome']}! 👋")
    
    tab_esforco, tab_agenda = st.tabs(["⚡ Esforço Hoje", "📅 Minha Agenda"])
    
    with tab_esforco:
        st.subheader("Controle de Atividades")
        st.info("Módulo de esforço carregado com sucesso.")

    with tab_agenda:
        st.subheader("Compromissos Agendados")
        st.write("Nenhum compromisso para hoje.")
