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
                except: logs[idx]['duracao_min'] = 0
            mudou = True
    if mudou:
        db.salvar_esforco(logs)

def exibir(user_info):
    st.title(f"Olá, {user_info['nome']}! 👋")
    
    # 1. Carregamento de dados
    diario = db.carregar_diario()
    atividades_log = db.carregar_esforco()
    motivos_gestao = db.carregar_motivos()
    hoje_dt = datetime.now().date()
    hoje_str = datetime.now().strftime("%d/%m/%Y")

    tab_esforco, tab_pendentes, tab_agenda, tab_novo = st.tabs([
        "⚡ Esforço Hoje", "🚀 Atividades Pendentes", "📅 Minha Agenda", "➕ Criar Lembrete"
    ])

    # --- ABA 1: GESTÃO DE ESFORÇO ---
    with tab_esforco:
        atv_ativa = next((a for a in atividades_log if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)
        c1, c2 = st.columns(2)
        with c1:
            if atv_ativa:
                st.info(f"🚀 **Ativo agora:**\n\n{atv_ativa['motivo']}")
                if st.button("Finalizar Agora", type="secondary", use_container_width=True):
                    finalizar_atividade_atual(user_info['nome'])
                    st.rerun()
            else: st.success("Pronto para começar uma nova tarefa!")
        
        with c2:
            motivo_sel = st.selectbox("O que vai fazer?", motivos_gestao)
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

    # --- ABA 2: PENDÊNCIAS (PESSOAL vs GERAL) ---
    with tab_pendentes:
        tipo_pnd = st.radio("Visualizar:", ["Minhas Pendências", "Geral (Equipe)"], horizontal=True)
        
        pendentes_lista = [i for i in diario if i.get('status') == "Pendente"]
        
        if tipo_pnd == "Minhas Pendências":
            exibir_pnd = [i for i in pendentes_lista if i.get('usuario') == user_info['nome']]
        else:
            exibir_pnd = pendentes_lista

        if exibir_pnd:
            for idx, item in enumerate(exibir_pnd):
                with st.container(border=True):
                    c_txt, c_btn = st.columns([4, 1])
                    c_txt.write(f"**[{item.get('depto', 'GERAL')}]** {item.get('solicitacao')}")
                    if item.get('usuario'): c_txt.caption(f"Solicitado por: {item['usuario']}")
                    
                    if c_btn.button("Feito", key=f"pnd_btn_{item.get('usuario')}_{idx}"):
                        item['status'] = "Executado"
                        db.salvar_diario(diario)
                        st.rerun()
        else:
            st.info("Nada pendente por aqui!")

    # --- ABA 3: AGENDA (PESSOAL vs EQUIPE) ---
    with tab_agenda:
        tipo_age = st.radio("Filtro de Agenda:", ["Minha Agenda", "Agenda da Equipe"], horizontal=True)
        
        agenda_dados = []
        for item in diario:
            if item.get('lembrete') and item['lembrete'] != "N/A":
                # Lógica de Filtro
                if tipo_age == "Minha Agenda" and item.get('usuario') != user_info['nome']:
                    continue
                
                agenda_dados.append({
                    "Data/Hora": item['lembrete'],
                    "O que": item['solicitacao'],
                    "Depto": item['depto'],
                    "Quem": item.get('usuario', 'S/I')
                })
        
        if agenda_dados:
            df_age = pd.DataFrame(agenda_dados).sort_values(by="Data/Hora")
            st.table(df_age)
        else:
            st.info("Nenhum compromisso agendado.")

    # --- ABA 4: NOVO LEMBRETE ---
    with tab_novo:
        st.subheader("➕ Criar Novo Lembrete")
        with st.form("form_novo_lembrete_home"):
            c_dep, c_dt, c_hr = st.columns([2, 1, 1])
            depto = c_dep.selectbox("Departamento", ["OPERAÇÃO", "TI", "RH", "LOGÍSTICA"])
            data_lembrete = c_dt.date_input("Data")
            hora_lembrete = c_hr.time_input("Hora")
            solic = st.text_area("O que precisa ser feito?")
            
            if st.form_submit_button("Salvar no Diário"):
                if solic:
                    novo_item = {
                        "usuario": user_info['nome'],
                        "depto": depto,
                        "solicitacao": solic,
                        "status": "Pendente",
                        "data": hoje_str,
                        "lembrete": f"{data_lembrete.strftime('%d/%m/%Y')} {hora_lembrete.strftime('%H:%M')}"
                    }
                    diario.append(novo_item)
                    db.salvar_diario(diario)
                    st.success("Lembrete agendado!")
                    st.rerun()
