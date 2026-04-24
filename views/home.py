import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from modulos import database as db  # Ajuste o caminho conforme sua estrutura

def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0: return "0min"
    horas = int(minutos // 60)
    mins = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"

def finalizar_atividade_atual(nome_usuario):
    logs = db.carregar_esforco()
    mudou = False
    agora = datetime.now()
    for idx, act in enumerate(logs):
        if act['usuario'] == nome_usuario and act['status'] == 'Em andamento':
            logs[idx]['fim'] = agora.isoformat()
            logs[idx]['status'] = 'Finalizado'
            inicio_str = act.get('inicio')
            if inicio_str:
                try:
                    inicio_dt = datetime.fromisoformat(inicio_str).replace(tzinfo=None)
                    duracao = (agora - inicio_dt).total_seconds() / 60
                    logs[idx]['duracao_min'] = round(duracao, 2)
                except: logs[idx]['duracao_min'] = 0
            mudou = True
    if mudou:
        db.salvar_esforco(logs)

def exibir(user_info):
    """Esta função substitui a antiga exibir_home() da main"""
    st.title(f"Olá, {user_info['nome']}! 👋")
    
    tab_esforco, tab_hoje, tab_agenda, tab_novo = st.tabs([
        "⚡ Esforço Hoje", "🚀 Atividades Pendentes", "📅 Minha Agenda", "➕ Criar Lembrete"
    ])

    # Carregamento de dados centralizado no módulo
    projs = db.carregar_projetos()
    diario = db.carregar_diario()
    atividades_log = db.carregar_esforco()
    motivos_gestao = db.carregar_motivos()
    hoje_dt = datetime.now().date()
    hoje_str = datetime.now().strftime("%d/%m/%Y")

    with tab_esforco:
        atv_ativa = next((a for a in atividades_log if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)
        c1, c2 = st.columns(2)
        with c1:
            if atv_ativa:
                st.info(f"🚀 **Ativo:** {atv_ativa['motivo']}")
                if st.button("Finalizar Agora", type="secondary", use_container_width=True):
                    finalizar_atividade_atual(user_info['nome'])
                    st.rerun()
            else: st.success("Pronto para começar!")
        with c2:
            motivo_sel = st.selectbox("O que vai fazer agora?", motivos_gestao)
            detalhes = st.text_input("Obs/Ticket")
            if st.button("INICIAR TAREFA", type="primary", use_container_width=True):
                finalizar_atividade_atual(user_info['nome'])
                atividades_log.append({
                    "usuario": user_info['nome'], "motivo": motivo_sel, 
                    "detalhes": detalhes, "inicio": datetime.now().isoformat(), 
                    "fim": None, "status": "Em andamento", "duracao_min": 0
                })
                db.salvar_esforco(atividades_log)
                st.rerun()

        st.divider()
        st.subheader("Minhas Atividades de Hoje")
        meu_hist = [a for a in atividades_log if a['usuario'] == user_info['nome']]
        if meu_hist:
            df_meu = pd.DataFrame(meu_hist)
            df_meu['inicio_dt'] = pd.to_datetime(df_meu['inicio'], errors='coerce')
            df_meu = df_meu.dropna(subset=['inicio_dt'])
            df_meu = df_meu[df_meu['inicio_dt'].dt.date == hoje_dt].copy()
            if not df_meu.empty:
                df_meu['Hora'] = df_meu['inicio_dt'].dt.strftime('%H:%M')
                df_meu['Tempo'] = df_meu['duracao_min'].apply(formatar_duracao_h_min)
                st.dataframe(df_meu[['Hora', 'motivo', 'detalhes', 'status', 'Tempo']], use_container_width=True, hide_index=True)

    with tab_hoje:
        # Coloque aqui a lógica dos cards de PQI e Diário que estava na main...
        # (A lógica que usa o container 'reminder-card' e 'diary-card')
        st.write("Pendências de Processos e Diário aparecem aqui.")

    with tab_agenda:
        # Lógica da Agenda que percorre projs e diario...
        st.write("Seus próximos compromissos.")

    with tab_novo:
        # Form de "Criar Agendamento Direto"...
        st.write("Crie novos lembretes aqui.")
