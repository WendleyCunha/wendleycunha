import streamlit as st
from modulos import database as db
from datetime import datetime

def exibir(user_info):
    st.markdown(f"<h1 class='gold-title'>Olá, {user_info['nome']}! 👋</h1>", unsafe_allow_html=True)
    
    tab_esforco, tab_agenda = st.tabs(["⚡ Registro de Esforço", "📅 Diário de Bordo"])
    
    with tab_esforco:
        # 1. Carregar logs existentes
        logs = db.carregar_esforco()
        
        # 2. Verificar se este usuário já tem algo rodando
        atv_ativa = next((a for a in logs if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)

        if not atv_ativa:
            st.subheader("Iniciar nova atividade")
            motivo = st.selectbox("O que vai fazer agora?", ["Monitoria", "Processos", "Reunião Tiago Costa", "BI/Dashboards"])
            detalhe = st.text_input("Alguma observação?")
            
            if st.button("▶️ INICIAR AGORA", use_container_width=True):
                nova_atv = {
                    "usuario": user_info['nome'],
                    "inicio": datetime.now().isoformat(),
                    "motivo": motivo,
                    "detalhe": detalhe,
                    "status": "Em andamento"
                }
                logs.append(nova_atv)
                db.salvar_esforco(logs)
                st.rerun()
        else:
            st.success(f"Você está em: **{atv_ativa['motivo']}**")
            st.info("Finalize no botão 'Parar' na barra lateral.")

    with tab_agenda:
        # Usando sua função carregar_diario()
        st.subheader("Anotações do Dia")
        diario = db.carregar_diario()
        
        texto_nota = st.text_area("Relate um aprendizado ou situação de hoje:")
        if st.button("Salvar no Diário"):
            nova_nota = {
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "usuario": user_info['nome'],
                "texto": texto_nota
            }
            diario.append(nova_nota)
            db.salvar_diario(diario)
            st.success("Nota salva com sucesso!")
