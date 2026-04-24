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
    # --- Estilos Originais ---
    st.markdown("""
        <style>
        .reminder-card {
            background: white; padding: 15px; border-radius: 10px;
            border-left: 5px solid #ef4444; margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .diary-card {
            background: white; padding: 15px; border-radius: 10px;
            border-left: 5px solid #3b82f6; margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title(f"Olá, {user_info['nome']}! 👋")
    
    # Carga de dados
    projs = db.carregar_projetos()
    diario = db.carregar_diario()
    atividades_log = db.carregar_esforco()
    motivos_gestao = db.carregar_motivos()
    hoje_dt = datetime.now().date()
    hoje_str = datetime.now().strftime("%d/%m/%Y")

    tab_esforco, tab_pendentes, tab_agenda, tab_novo = st.tabs([
        "⚡ Esforço Hoje", "🚀 Atividades Pendentes", "📅 Minha Agenda", "➕ Criar Lembrete"
    ])

    # --- ABA 1: ESFORÇO (Com contador de tempo) ---
    with tab_esforco:
        atv_ativa = next((a for a in atividades_log if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'), None)
        c1, c2 = st.columns(2)
        with c1:
            if atv_ativa:
                st.info(f"🚀 **Ativo:** {atv_ativa['motivo']}")
                try:
                    inicio_dt = datetime.fromisoformat(atv_ativa['inicio']).replace(tzinfo=None)
                    decorrido = (datetime.now() - inicio_dt).seconds // 60
                    st.write(f"Desde {inicio_dt.strftime('%H:%M')} ({decorrido} min)")
                except: st.write("Iniciado agora")
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
                    "usuario": user_info['nome'], "motivo": motivo_sel, "detalhes": detalhes, 
                    "inicio": datetime.now().isoformat(), "fim": None, "status": "Em andamento", "duracao_min": 0
                })
                db.salvar_esforco(atividades_log)
                st.rerun()

        st.divider()
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

    # --- ABA 2: PENDÊNCIAS (PQI + DIÁRIO + FILTROS) ---
    with tab_pendentes:
        tipo_pnd = st.radio("Visualizar:", ["Minhas Pendências", "Geral (Equipe)"], horizontal=True)
        
        col_pqi, col_dir = st.columns(2)
        
        with col_pqi:
            st.subheader("📌 Processos (PQI)")
            for p_idx, p in enumerate(projs):
                if 'lembretes' in p:
                    for l_idx, l in enumerate(p['lembretes']):
                        data_l_dt = datetime.strptime(l['data_hora'].split(" ")[0], "%d/%m/%Y").date()
                        if data_l_dt <= hoje_dt:
                            # Filtro pessoal opcional: se o PQI tiver dono, você pode filtrar aqui
                            is_atrasada = data_l_dt < hoje_dt
                            st.markdown(f'''
                                <div class="reminder-card" style="border-left-color: {"#f87171" if is_atrasada else "#ef4444"};">
                                    <small style="color:{"#f87171" if is_atrasada else "#ef4444"}; font-weight:bold;">{"⚠️ ATRASADA" if is_atrasada else "⏰ HOJE"}</small><br>
                                    <strong>Projeto:</strong> {p["titulo"]}<br>
                                    <strong>Tarefa:</strong> {l["texto"]}
                                </div>
                            ''', unsafe_allow_html=True)
                            if st.button("Concluir PQI", key=f"pnd_pqi_{p_idx}_{l_idx}"):
                                p['lembretes'].pop(l_idx)
                                db.salvar_projetos(projs)
                                st.rerun()

        with col_dir:
            st.subheader("📓 Diário")
            for idx, sit in enumerate(diario):
                if sit.get('status') == "Pendente" and sit.get('lembrete') != "N/A":
                    # Lógica de Filtro Novo
                    if tipo_pnd == "Minhas Pendências" and sit.get('usuario') != user_info['nome']:
                        continue
                    
                    data_s_dt = datetime.strptime(sit['lembrete'].split(" ")[0], "%d/%m/%Y").date()
                    if data_s_dt <= hoje_dt:
                        is_atrasada = data_s_dt < hoje_dt
                        st.markdown(f'''
                            <div class="diary-card">
                                <small style="color:{'#ef4444' if is_atrasada else '#3b82f6'}; font-weight:bold;">{"🚨 ATRASADO" if is_atrasada else "📅 AGENDADO"}</small><br>
                                <strong>Solicitação:</strong> {sit["solicitacao"]}<br>
                                <strong>Depto:</strong> {sit["depto"]} | <strong>Por:</strong> {sit.get('usuario','S/I')}
                            </div>
                        ''', unsafe_allow_html=True)
                        if st.button("Executado", key=f"pnd_dir_{idx}"):
                            sit['status'] = "Executado"
                            db.salvar_diario(diario)
                            st.rerun()

    # --- ABA 3: AGENDA (PESSOAL vs EQUIPE) ---
    with tab_agenda:
        tipo_age = st.radio("Filtro de Agenda:", ["Minha Agenda", "Agenda da Equipe"], horizontal=True)
        agenda_data = []
        # Coleta PQI
        for p in projs:
            for l in p.get('lembretes', []):
                if l['data_hora'].split(" ")[0] > hoje_str:
                    agenda_data.append({"Data": l['data_hora'].split(" ")[0], "Origem": f"PQI: {p['titulo']}", "Descrição": l['texto'], "Quem": "Equipe"})
        # Coleta Diário
        for sit in diario:
            if sit.get('status') == "Pendente" and sit.get('lembrete', "N/A") != "N/A":
                data_limpa = sit['lembrete'].split(" ")[0]
                if data_limpa > hoje_str:
                    # Filtro
                    if tipo_age == "Minha Agenda" and sit.get('usuario') != user_info['nome']:
                        continue
                    agenda_data.append({"Data": data_limpa, "Origem": f"DIÁRIO: {sit['depto']}", "Descrição": sit['solicitacao'], "Quem": sit.get('usuario', 'S/I')})
        
        if agenda_data:
            df_age = pd.DataFrame(agenda_data).sort_values(by="Data")
            st.dataframe(df_age, use_container_width=True, hide_index=True)
        else: st.info("Sem compromissos futuros.")

    # --- ABA 4: NOVO (VINCULADO) ---
    with tab_novo:
        st.subheader("🎯 Criar Agendamento Direto")
        with st.form("form_novo_main"):
            tipo = st.radio("Vincular a:", ["Processos (PQI)", "Situações Diárias (Diário)"], horizontal=True)
            txt_lembrete = st.text_input("O que precisa ser feito?")
            c_data, c_hora = st.columns(2)
            d_agendada = c_data.date_input("Data do Lembrete")
            h_agendada = c_hora.time_input("Hora do Lembrete")
            proj_vinc = st.selectbox("Projeto (Se PQI):", [p['titulo'] for p in projs]) if tipo == "Processos (PQI)" else None
            
            if st.form_submit_button("Gerar Lembrete 🚀", use_container_width=True):
                data_f = f"{d_agendada.strftime('%d/%m/%Y')} {h_agendada.strftime('%H:%M')}"
                if tipo == "Processos (PQI)":
                    for p in projs:
                        if p['titulo'] == proj_vinc:
                            p.setdefault('lembretes', []).append({"id": datetime.now().timestamp(), "data_hora": data_f, "texto": txt_lembrete, "status": "Pendente"})
                    db.salvar_projetos(projs)
                else:
                    diario.append({"usuario": user_info['nome'], "data_reg": datetime.now().strftime("%d/%m/%Y %H:%M"), "solicitacao": txt_lembrete, "depto": "GERAL", "lembrete": data_f, "status": "Pendente"})
                    db.salvar_diario(diario)
                st.success("Agendado!"); st.rerun()
