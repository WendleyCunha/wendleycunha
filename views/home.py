import streamlit as st
import pandas as pd
from datetime import datetime
from modulos import database as db

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
                except:
                    logs[idx]['duracao_min'] = 0
            mudou = True
    if mudou:
        db.salvar_esforco(logs)

def exibir(user_info):
    """Função principal da Home que gerencia o dashboard do usuário"""
    st.title(f"Olá, {user_info['nome']}! 👋")
    
    # 1. Carregamento de dados centralizado
    projs = db.carregar_projetos()
    diario = db.carregar_diario()
    atividades_log = db.carregar_esforco()
    
    # Tenta carregar motivos, se falhar usa lista padrão
    try:
        motivos_gestao = db.carregar_motivos()
    except:
        motivos_gestao = ["PROJETO", "REUNIÃO", "OPERACIONAL", "OUTROS"]
        
    hoje_dt = datetime.now().date()
    hoje_str = datetime.now().strftime("%d/%m/%Y")

    tab_esforco, tab_hoje, tab_agenda, tab_novo = st.tabs([
        "⚡ Esforço Hoje", "🚀 Atividades Pendentes", "📅 Minha Agenda", "➕ Criar Lembrete"
    ])

    # --- ABA 1: GESTÃO DE ESFORÇO ---
    with tab_esforco:
        atv_ativa = next((a for a in atividades_log if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)
        c1, c2 = st.columns(2)
        
        with c1:
            if atv_ativa:
                st.info(f"🚀 **Ativo:** {atv_ativa['motivo']}")
                if st.button("Finalizar Agora", type="secondary", use_container_width=True):
                    finalizar_atividade_atual(user_info['nome'])
                    st.rerun()
            else:
                st.success("Pronto para começar uma nova tarefa!")
                
        with c2:
            motivo_sel = st.selectbox("O que vai fazer agora?", motivos_gestao)
            detalhes = st.text_input("Observação ou Ticket")
            if st.button("INICIAR TAREFA", type="primary", use_container_width=True):
                finalizar_atividade_atual(user_info['nome'])
                atividades_log.append({
                    "usuario": user_info['nome'], 
                    "motivo": motivo_sel, 
                    "detalhes": detalhes, 
                    "inicio": datetime.now().isoformat(), 
                    "fim": None, 
                    "status": "Em andamento", 
                    "duracao_min": 0
                })
                db.salvar_esforco(atividades_log)
                st.rerun()

        st.divider()
        st.subheader("Meu Histórico de Hoje")
        meu_hist = [a for a in atividades_log if a['usuario'] == user_info['nome']]
        if meu_hist:
            df_meu = pd.DataFrame(meu_hist)
            df_meu['inicio_dt'] = pd.to_datetime(df_meu['inicio'], errors='coerce')
            df_meu = df_meu.dropna(subset=['inicio_dt'])
            df_meu = df_meu[df_meu['inicio_dt'].dt.date == hoje_dt].copy()
            
            if not df_meu.empty:
                df_meu['Hora'] = df_meu['inicio_dt'].dt.strftime('%H:%M')
                df_meu['Tempo'] = df_meu['duracao_min'].apply(formatar_duracao_h_min)
                st.dataframe(
                    df_meu[['Hora', 'motivo', 'detalhes', 'status', 'Tempo']], 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.caption("Nenhuma atividade registrada hoje.")

    # --- ABA 2: PENDÊNCIAS (PQI + DIÁRIO) ---
    with tab_hoje:
        col_pqi, col_dir = st.columns(2)
        
        with col_pqi:
            st.subheader("📌 Processos (PQI)")
            tem_pqi = False
            for p_idx, p in enumerate(projs):
                if 'lembretes' in p:
                    for l_idx, l in enumerate(p['lembretes']):
                        try:
                            data_l_str = l['data_hora'].split(" ")[0]
                            data_l_dt = datetime.strptime(data_l_str, "%d/%m/%Y").date()
                            if data_l_dt <= hoje_dt:
                                tem_pqi = True
                                with st.container(border=True):
                                    st.write(f"**{p['titulo']}**")
                                    st.caption(l['texto'])
                                    if st.button("Concluir", key=f"pqi_{p_idx}_{l_idx}"):
                                        p['lembretes'].pop(l_idx)
                                        db.salvar_projetos(projs)
                                        st.rerun()
                        except: continue
            if not tem_pqi: st.info("Nenhum processo pendente.")

        with col_dir:
            st.subheader("📓 Diário")
            tem_diario = False
            for idx, item in enumerate(diario):
                if item.get('status') == "Pendente":
                    tem_diario = True
                    with st.container(border=True):
                        st.write(f"**{item['depto']}**")
                        st.write(item['solicitacao'])
                        if st.button("Feito", key=f"dir_{idx}"):
                            item['status'] = "Executado"
                            db.salvar_diario(diario)
                            st.rerun()
            if not tem_diario: st.info("Diário está limpo.")

    # --- ABA 3: AGENDA ---
    with tab_agenda:
        st.subheader("📅 Próximos Compromissos")
        agenda_dados = []
        for item in diario:
            if item.get('lembrete') and item['lembrete'] != "N/A":
                agenda_dados.append({
                    "Data/Hora": item['lembrete'],
                    "Assunto": item['solicitacao'],
                    "Setor": item['depto']
                })
        
        if agenda_dados:
            st.table(pd.DataFrame(agenda_dados))
        else:
            st.info("Nenhum compromisso agendado.")

    # --- ABA 4: NOVO LEMBRETE ---
    with tab_novo:
        st.subheader("➕ Agendar Nova Pendência")
        with st.form("form_novo_lembrete_home"):
            depto_sel = st.selectbox("Departamento", ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA", "OUTROS"])
            solic_text = st.text_area("O que precisa ser feito?")
            c_data, c_hora = st.columns(2)
            data_ag = c_data.date_input("Data do Lembrete")
            hora_ag = c_hora.time_input("Hora do Lembrete")
            
            if st.form_submit_button("Salvar no Diário"):
                novo_item = {
                    "usuario": user_info['nome'],
                    "depto": depto_sel,
                    "solicitacao": solic_text,
                    "status": "Pendente",
                    "data": hoje_str,
                    "lembrete": f"{data_ag.strftime('%d/%m/%Y')} {hora_ag.strftime('%H:%M')}"
                }
                diario.append(novo_item)
                db.salvar_diario(diario)
                st.success("Lembrete salvo com sucesso!")
                st.rerun()
