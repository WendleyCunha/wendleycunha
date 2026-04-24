import streamlit as st
from modulos import database as db
from datetime import datetime

def exibir(user_info):
    st.markdown(f"<h1 style='color: #D4AF37;'>Olá, {user_info['nome']}! 👋</h1>", unsafe_allow_html=True)
    
    tab_esforco, tab_agenda = st.tabs(["⚡ Esforço & Atividades", "📅 Diário e Avisos"])
    
    with tab_esforco:
        st.subheader("O que você está fazendo agora?")
        # Carrega logs para verificar se já existe algo em andamento
        logs = db.carregar_esforco()
        atv_ativa = next((a for a in logs if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)

        if not atv_ativa:
            # Opções de atividades baseadas no seu dia a dia na King Star
            motivo = st.selectbox("Selecione a tarefa:", 
                                ["Monitoria de Qualidade", "Mapeamento de Processo", 
                                 "Reunião Tiago Costa", "Ajuste de Dashboard", "Treinamento", "Outros"])
            detalhe = st.text_input("Detalhe da tarefa (opcional)")
            
            if st.button("▶️ INICIAR ESFORÇO", use_container_width=True):
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
            st.success(f"Tarefa em curso: **{atv_ativa['motivo']}**")
            st.info("Você pode encerrar esta tarefa no menu lateral a qualquer momento.")

    with tab_agenda:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📢 Avisos e Lembretes")
            lembretes = db.carregar_lembretes() # Certifique-se que essa função existe no database.py
            for l in lembretes:
                st.markdown(f"""<div class="reminder-card">
                    <strong>{l['titulo']}</strong><br>{l['texto']}
                </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown("### ✍️ Meu Diário de Bordo")
            nota = st.text_area("O que aprendeu ou resolveu hoje?", placeholder="Ex: Resolvido gargalo na logística...")
            if st.button("Salvar Nota"):
                # Lógica para salvar no Firebase ou JSON
                st.toast("Nota salva com sucesso!")
