import streamlit as st
import database as db  # Ajuste conforme sua pasta
from datetime import datetime

def exibir(user_info):
    st.markdown(f"<h1 class='gold-title'>Olá, {user_info['nome']}! 👋</h1>", unsafe_allow_html=True)
    
    tab_esforco, tab_agenda = st.tabs(["⚡ Registro de Esforço", "📅 Diário de Bordo"])
    
    with tab_esforco:
        logs = db.carregar_esforco()
        atv_ativa = next((a for a in logs if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)

        if not atv_ativa:
            with st.container(border=True):
                st.subheader("Iniciar nova atividade")
                motivo = st.selectbox("O que vai fazer agora?", ["Monitoria", "Processos", "Reunião Tiago Costa", "BI/Dashboards", "Manutenção Spin"])
                detalhe = st.text_input("Alguma observação?")
                
                if st.button("▶️ INICIAR AGORA", use_container_width=True, type="primary"):
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
            st.info(f"🚀 Atividade em curso: **{atv_ativa['motivo']}**")
            st.caption("Para encerrar, use o botão 'Parar Agora' no menu lateral.")

    with tab_agenda:
        st.subheader("Anotações do Dia")
        diario = db.carregar_diario()
        
        with st.expander("✍️ Nova Anotação", expanded=True):
            texto_nota = st.text_area("O que aconteceu de relevante hoje?", placeholder="Ex: Finalizei o dashboard de logística...")
            if st.button("Salvar no Diário", use_container_width=True):
                if texto_nota:
                    nova_nota = {
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "usuario": user_info['nome'],
                        "texto": texto_nota
                    }
                    diario.append(nova_nota)
                    db.salvar_diario(diario)
                    st.success("Nota salva!")
                    st.rerun()

        st.markdown("---")
        # Exibição das notas com o Estilo CSS que criamos
        for nota in reversed(diario[-10:]): # Mostra as últimas 10
            st.markdown(f"""
                <div class="diary-card">
                    <small>{nota['data']} - {nota['usuario']}</small><br>
                    {nota['texto']}
                </div>
            """, unsafe_allow_html=True)
