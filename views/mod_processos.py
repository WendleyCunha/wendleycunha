import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from modulos import database as db

# --- CONFIGURAÇÕES DO ROADMAP ---
ROADMAP = [
    {"id": 1, "nome": "Triagem & GUT"}, {"id": 2, "nome": "Escopo & Charter"},
    {"id": 3, "nome": "Autorização Sponsor"}, {"id": 4, "nome": "Coleta & Impedimentos"},
    {"id": 5, "nome": "Modelagem & Piloto"}, {"id": 6, "nome": "Migração (Go-Live)"},
    {"id": 7, "nome": "Acompanhamento/Ajuste"}, {"id": 8, "nome": "Padronização & POP"}
]

MOTIVOS_PADRAO = ["Reunião", "Pedido de Posicionamento", "Elaboração de Documentos", "Anotação Interna (Sem Dash)"]
DEPARTAMENTOS = ["CX", "PQI", "Compras", "Logística", "TI", "Financeiro", "RH", "Fiscal", "Operações", "Comercial", "Diretoria"]


def exibir(user_role="OPERACIONAL"):

    # 1. ESTILO CSS
    st.markdown("""
    <style>
        .metric-card { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #ececec; text-align: center; }
        .metric-value { font-size: 24px; font-weight: 800; color: #002366; }
        .metric-label { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }
        .ponto-regua { width: 30px; height: 30px; border-radius: 50%; background: #e2e8f0; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #64748b; margin: 0 auto; border: 2px solid #cbd5e1; font-size: 12px;}
        .ponto-check { background: #10b981; color: white; border-color: #10b981; }
        .ponto-atual { background: #002366; color: white; border-color: #002366; box-shadow: 0 0 8px rgba(0, 35, 102, 0.4); }
        .label-regua { font-size: 9px; text-align: center; font-weight: bold; margin-top: 5px; color: #475569; height: 25px; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)

    # 2. INICIALIZAÇÃO DE DADOS
    if 'db_pqi' not in st.session_state:
        dados_pqi = db.carregar_projetos()
        st.session_state.db_pqi = dados_pqi if isinstance(dados_pqi, list) else []

    if 'situacoes_diarias' not in st.session_state:
        dados_diario = db.carregar_diario()
        st.session_state.situacoes_diarias = dados_diario if isinstance(dados_diario, list) else []

    def salvar_seguro():
        try:
            db.salvar_projetos(st.session_state.db_pqi)
            db.salvar_diario(st.session_state.situacoes_diarias)
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    # --- DEFINIÇÃO DAS ABAS ---
    titulos = ["📊 DASHBOARD GERAL"]
    if user_role in ["ADM", "GERENTE"]:
        titulos.append("⚙️ GESTÃO")
    titulos.append("🚀 OPERAÇÃO PQI")

    tabs = st.tabs(titulos)
    tab_dash = tabs[0]

    if user_role in ["ADM", "GERENTE"]:
        tab_gestao = tabs[1]
        tab_operacao = tabs[2]
    else:
        tab_gestao = None
        tab_operacao = tabs[1]

    # =========================================================
    # --- 1. DASHBOARD GERAL ---
    # =========================================================
    with tab_dash:
        sub_d1, sub_d2 = st.tabs(["📈 Portfólio Ativo", "✅ Projetos Entregues"])
        projs = st.session_state.db_pqi

        with sub_d1:
            ativos = [p for p in projs if p.get('status') != "Concluído"]
            if ativos:
                c1, c2, c3 = st.columns(3)
                c1.markdown(f'<div class="metric-card"><div class="metric-label">Projetos Ativos</div><div class="metric-value">{len(ativos)}</div></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="metric-card"><div class="metric-label">Total de Ações</div><div class="metric-value">{sum(len(p.get("notas", [])) for p in ativos)}</div></div>', unsafe_allow_html=True)

                todas_notas = [n for p in ativos for n in p.get('notas', [])]
                df_notas = pd.DataFrame(todas_notas)
                gargalo = "N/A"
                if not df_notas.empty and 'depto' in df_notas.columns:
                    valid_deptos = df_notas['depto'].dropna()
                    if not valid_deptos.empty:
                        gargalo = valid_deptos.mode().iloc[0]
                c3.markdown(f'<div class="metric-card"><div class="metric-label">Gargalo (Depto)</div><div class="metric-value" style="font-size:18px">{gargalo}</div></div>', unsafe_allow_html=True)

                st.write("")
                df_at = pd.DataFrame([
                    {"Projeto": p.get('titulo', 'Sem Título'), "Fase": f"Fase {p.get('fase', 1)}", "Esforço": len(p.get('notas', []))}
                    for p in ativos
                ])

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("##### 📊 Esforço por Projeto")
                    st.bar_chart(df_at.set_index("Projeto")["Esforço"])
                with col_g2:
                    st.markdown("##### 🍕 Participação")
                    fig_pizza = px.pie(df_at, values='Esforço', names='Projeto', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
                    fig_pizza.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300, showlegend=True)
                    st.plotly_chart(fig_pizza, use_container_width=True)

                st.divider()
                st.markdown("##### 📋 Detalhamento do Portfólio")
                st.dataframe(df_at, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum projeto ativo.")

        with sub_d2:
            concluidos = [p for p in projs if p.get('status') == "Concluído"]
            if concluidos:
                df_concl = pd.DataFrame([
                    {
                        "Projeto": p['titulo'],
                        # FIX 1: campo data_conclusao agora é corretamente exibido
                        "Data Conclusão": p.get('data_conclusao', 'S/D'),
                        "Ações": len(p.get('notas', []))
                    }
                    for p in concluidos
                ])
                st.dataframe(df_concl, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum projeto entregue.")

    # =========================================================
    # --- 2. GESTÃO ---
    # =========================================================
    if tab_gestao:
        with tab_gestao:
            sub_g1, sub_g2 = st.tabs(["⚙️ Gerenciamento de Projetos", "📝 Situações Diárias"])

            with sub_g1:
                if st.button("➕ CRIAR NOVO PROJETO PQI", type="primary", use_container_width=True):
                    novo_projeto = {
                        "titulo": f"Novo Projeto {len(st.session_state.db_pqi) + 1}",
                        "fase": 1, "status": "Ativo", "notas": [], "lembretes": [],
                        "pastas_virtuais": {}, "motivos_custom": [], "checklist": [],
                        "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "data_conclusao": None
                    }
                    st.session_state.db_pqi.append(novo_projeto)
                    salvar_seguro()
                    st.rerun()

                st.write("---")
                for i, proj_gest in enumerate(st.session_state.db_pqi):
                    with st.expander(f"Configurações: {proj_gest['titulo']}"):
                        col_cfg1, col_cfg2 = st.columns([2, 1])
                        novo_titulo = col_cfg1.text_input(
                            "Nome do Projeto",
                            proj_gest['titulo'],
                            key=f"gest_t_{i}"
                        )
                        stts_options = ["Ativo", "Concluído", "Pausado"]
                        novo_status = col_cfg2.selectbox(
                            "Status",
                            stts_options,
                            index=stts_options.index(proj_gest.get('status', 'Ativo')),
                            key=f"gest_s_{i}"
                        )

                        # FIX 2: motivos_custom pré-populados com valores atuais
                        motivos_atuais = ", ".join(proj_gest.get('motivos_custom', []))
                        st.write("**Motivos Customizados**")
                        novos_mots = st.text_input(
                            "Adicionar motivos (separados por vírgula)",
                            value=motivos_atuais,
                            key=f"mot_cust_{i}"
                        )

                        col_save, col_del = st.columns([3, 1])

                        # FIX 3: botão de salvar explícito para título, status e motivos
                        if col_save.button("💾 Salvar Alterações", key=f"gest_save_{i}", use_container_width=True, type="primary"):
                            proj_gest['titulo'] = novo_titulo
                            # FIX 4: grava data_conclusao quando status muda para Concluído
                            status_anterior = proj_gest.get('status', 'Ativo')
                            proj_gest['status'] = novo_status
                            if novo_status == "Concluído" and status_anterior != "Concluído":
                                proj_gest['data_conclusao'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                            elif novo_status != "Concluído":
                                proj_gest['data_conclusao'] = None
                            proj_gest['motivos_custom'] = [m.strip() for m in novos_mots.split(",") if m.strip()]
                            salvar_seguro()
                            st.success("Projeto atualizado!")
                            st.rerun()

                        if col_del.button("🗑️ Excluir", key=f"gest_del_{i}", use_container_width=True):
                            st.session_state.db_pqi.pop(i)
                            salvar_seguro()
                            st.rerun()

            # ---------------------------------------------------------
            with sub_g2:
                st.subheader("📓 Diário de Situações")
                with st.container(border=True):
                    col_sit1, col_sit2 = st.columns([2, 1])
                    titulo_sit = col_sit1.text_input("O que pediram?")
                    depto_sit = col_sit2.selectbox("Quem pediu?", DEPARTAMENTOS, key="depto_sit_diario")
                    desc_sit = st.text_area("Detalhes da ação")

                    st.write("**⏰ Agendar Lembrete?**")
                    cl_d1, cl_d2 = st.columns(2)
                    dl_sit = cl_d1.date_input("Data Limite", value=None, key="date_sit_diario")
                    hl_sit = cl_d2.time_input("Hora Limite", value=None, key="time_sit_diario")

                    if st.button("Gravar no Diário", type="primary"):
                        if titulo_sit:
                            nova_sit = {
                                "id": datetime.now().timestamp(),
                                "data_reg": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "solicitacao": titulo_sit, "depto": depto_sit, "detalhes": desc_sit,
                                "lembrete": f"{dl_sit.strftime('%d/%m/%Y')} {hl_sit.strftime('%H:%M')}" if dl_sit and hl_sit else "N/A",
                                "status": "Pendente", "obs_final": ""
                            }
                            st.session_state.situacoes_diarias.append(nova_sit)
                            salvar_seguro()
                            st.success("Demanda registrada!")
                            st.rerun()
                        else:
                            st.warning("Informe o título da solicitação.")

                st.divider()
                if st.session_state.situacoes_diarias:
                    ver_status = st.multiselect(
                        "Filtrar Status:",
                        ["Pendente", "Executado", "Cancelado", "Não Possível"],
                        default=["Pendente"]
                    )

                    for idx, sit in enumerate(st.session_state.situacoes_diarias):
                        if not ver_status or sit.get('status', 'Pendente') in ver_status:
                            cor_status = {"Pendente": "🔵", "Executado": "✅", "Cancelado": "❌", "Não Possível": "⚠️"}
                            solicitacao = sit.get('solicitacao', 'Sem Título')
                            depto = sit.get('depto', 'Geral')
                            data_reg = sit.get('data_reg', '--/--')
                            lembrete = sit.get('lembrete', 'Sem lembrete')
                            detalhes_texto = sit.get('detalhes', 'Nenhum detalhe informado.')
                            status_atual = sit.get('status', 'Pendente')

                            with st.expander(f"{cor_status.get(status_atual, '⚪')} {solicitacao} | {depto}"):
                                st.write(f"**Registrado:** {data_reg} | **Lembrete:** {lembrete}")
                                st.info(f"**Detalhes:** {detalhes_texto}")

                                # FIX 5: exibe obs_final quando situação não está mais pendente
                                if status_atual != "Pendente" and sit.get('obs_final'):
                                    st.caption(f"📝 Observação: {sit['obs_final']}")

                                if status_atual == "Pendente":
                                    # FIX 6: c_btn3 agora implementado com "Não Possível"
                                    c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)

                                    if c_btn1.button("✅ Executado", key=f"ok_{idx}"):
                                        st.session_state.situacoes_diarias[idx]['status'] = "Executado"
                                        salvar_seguro()
                                        st.rerun()

                                    with c_btn2.popover("❌ Cancelar"):
                                        motivo_canc = st.text_input("Motivo", key=f"txt_cnc_{idx}")
                                        if st.button("Confirmar", key=f"btn_cnc_{idx}"):
                                            st.session_state.situacoes_diarias[idx]['status'] = "Cancelado"
                                            st.session_state.situacoes_diarias[idx]['obs_final'] = motivo_canc
                                            salvar_seguro()
                                            st.rerun()

                                    # FIX 6 (cont.): botão "Não Possível" antes inexistente
                                    with c_btn3.popover("⚠️ Não Possível"):
                                        motivo_np = st.text_input("Motivo", key=f"txt_np_{idx}")
                                        if st.button("Confirmar", key=f"btn_np_{idx}"):
                                            st.session_state.situacoes_diarias[idx]['status'] = "Não Possível"
                                            st.session_state.situacoes_diarias[idx]['obs_final'] = motivo_np
                                            salvar_seguro()
                                            st.rerun()

                                    if c_btn4.button("🗑️ Excluir", key=f"del_sit_{idx}"):
                                        st.session_state.situacoes_diarias.pop(idx)
                                        salvar_seguro()
                                        st.rerun()

    # =========================================================
    # --- 3. OPERAÇÃO PQI ---
    # =========================================================
    with tab_operacao:
        st.subheader("🚀 Operação de Processos")
        projs = st.session_state.db_pqi
        if not projs:
            st.warning("Crie um projeto na aba GESTÃO.")
        else:
            c_f1, c_f2 = st.columns([1, 2])
            status_sel = c_f1.radio("Filtro:", ["🚀 Ativos", "✅ Concluídos", "⏸️ Pausados"], horizontal=True)
            map_status = {"🚀 Ativos": "Ativo", "✅ Concluídos": "Concluído", "⏸️ Pausados": "Pausado"}
            filtrados = [p for p in projs if p.get('status', 'Ativo') == map_status[status_sel]]

            if filtrados:
                proj_escolha = c_f2.selectbox("Selecione o Projeto:", [p['titulo'] for p in filtrados])
                projeto = next(p for p in filtrados if p['titulo'] == proj_escolha)

                st.write("")
                cols_r = st.columns(8)
                for i, etapa in enumerate(ROADMAP):
                    n, cl, txt = i + 1, "ponto-regua", str(i + 1)
                    if n < projeto['fase']:
                        cl += " ponto-check"; txt = "✔"
                    elif n == projeto['fase']:
                        cl += " ponto-atual"
                    cols_r[i].markdown(f'<div class="{cl}">{txt}</div><div class="label-regua">{etapa["nome"]}</div>', unsafe_allow_html=True)

                t_exec, t_dossie, t_esforco = st.tabs(["📝 Execução Diária", "📁 Dossiê", "📊 Análise"])

                # =====================================================
                with t_exec:
                    col_e1, col_e2 = st.columns([2, 1])

                    with col_e1:
                        st.markdown(f"### Etapa {projeto['fase']}: {ROADMAP[projeto['fase'] - 1]['nome']}")

                        with st.popover("➕ Adicionar Registro", use_container_width=True):
                            c_p1, c_p2 = st.columns(2)
                            mot = c_p1.selectbox("Assunto", MOTIVOS_PADRAO + projeto.get('motivos_custom', []))
                            dep = c_p2.selectbox("Departamento", DEPARTAMENTOS)
                            dsc = st.text_area("Descrição")
                            dl = st.date_input("Lembrete", value=None, key=f"d_pqi_{projeto['titulo']}")
                            hl = st.time_input("Hora", value=None, key=f"h_pqi_{projeto['titulo']}")
                            if st.button("Gravar no Banco", type="primary"):
                                if dl and hl:
                                    projeto.setdefault('lembretes', []).append({
                                        "id": datetime.now().timestamp(),
                                        "data_hora": f"{dl.strftime('%d/%m/%Y')} {hl.strftime('%H:%M')}",
                                        "texto": f"{projeto['titulo']}: {mot}"
                                    })
                                projeto['notas'].append({
                                    "motivo": mot, "depto": dep, "texto": dsc,
                                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                    "fase_origem": projeto['fase']
                                })
                                salvar_seguro()
                                st.rerun()

                        st.divider()
                        notas_fase = [n for n in projeto.get('notas', []) if n.get('fase_origem') == projeto['fase']]
                        for n in reversed(notas_fase):
                            with st.expander(f"📌 {n['motivo']} - {n['data']}"):
                                st.write(n['texto'])

                        st.divider()
                        st.markdown("#### 📋 Checklist de Atividades da Etapa")

                        with st.popover("➕ Nova Atividade", use_container_width=True):
                            c_chk1, c_chk2 = st.columns([2, 1])
                            txt_tarefa = c_chk1.text_input("Atividade/Tarefa")
                            resp_tarefa = c_chk2.selectbox("Responsável", ["Wendley Cunha", "Guilherme Egidio", "Tiago Costa", "Willian Diego", "Valdjane Maria", "Danilo Mesquita", "Ariadne Barreto", "Allan Barros", "Outro"])

                            c_chk3, c_chk4 = st.columns(2)
                            dt_tarefa = c_chk3.date_input("Prazo", key=f"dt_chk_{projeto['titulo']}")
                            hr_tarefa = c_chk4.time_input("Hora", key=f"hr_chk_{projeto['titulo']}")

                            if st.button("Agendar Atividade", type="primary", use_container_width=True):
                                if txt_tarefa:
                                    nova_atividade = {
                                        "id": datetime.now().timestamp(),
                                        "tarefa": txt_tarefa,
                                        "responsavel": resp_tarefa,
                                        "prazo": f"{dt_tarefa.strftime('%d/%m/%Y')} {hr_tarefa.strftime('%H:%M')}",
                                        "status": "Pendente",
                                        "fase_origem": projeto['fase']
                                    }
                                    projeto.setdefault('checklist', []).append(nova_atividade)
                                    projeto.setdefault('lembretes', []).append({
                                        "id": datetime.now().timestamp(),
                                        "data_hora": f"{dt_tarefa.strftime('%d/%m/%Y')} {hr_tarefa.strftime('%H:%M')}",
                                        "texto": f"CHECKLIST [{resp_tarefa}]: {txt_tarefa}"
                                    })
                                    salvar_seguro()
                                    st.success("Atividade e Lembrete criados!")
                                    st.rerun()
                                else:
                                    st.warning("Informe o nome da atividade.")

                        # --- EXIBIÇÃO DO CHECKLIST ---
                        atividades_fase = [a for a in projeto.get('checklist', []) if a.get('fase_origem') == projeto['fase']]

                        if atividades_fase:
                            # FIX 7: contagem de progresso do checklist
                            total_ativ = len(atividades_fase)
                            concluidas_ativ = sum(1 for a in atividades_fase if a.get('status') == "Concluído")
                            st.progress(concluidas_ativ / total_ativ, text=f"{concluidas_ativ}/{total_ativ} atividades concluídas")

                            for idx_a, ativ in enumerate(atividades_fase):
                                with st.container(border=True):
                                    col_a, col_b, col_c = st.columns([0.1, 0.5, 0.4])

                                    is_concluido = ativ.get('status') == "Concluído"

                                    # FIX 8: checkbox bidirecional — marca E desmarca corretamente
                                    checkbox_val = col_a.checkbox("", key=f"chk_exec_{ativ['id']}_{idx_a}", value=is_concluido)

                                    if checkbox_val and not is_concluido:
                                        # Usuário marcou como concluído
                                        for item in projeto['checklist']:
                                            if item['id'] == ativ['id']:
                                                item['status'] = "Concluído"
                                                break
                                        salvar_seguro()
                                        st.rerun()
                                    elif not checkbox_val and is_concluido:
                                        # FIX 8 (cont.): usuário desmarcou — reverte para Pendente
                                        for item in projeto['checklist']:
                                            if item['id'] == ativ['id']:
                                                item['status'] = "Pendente"
                                                break
                                        salvar_seguro()
                                        st.rerun()

                                    status_style_open = "~~" if is_concluido else ""
                                    status_style_close = "~~" if is_concluido else ""
                                    qtd_p = ativ.get('prorrogacoes', 0)
                                    badge_p = f" ⚠️ *({qtd_p}x)*" if qtd_p > 0 else ""

                                    col_b.markdown(f"{status_style_open}**{ativ['tarefa']}** ({ativ['responsavel']}){status_style_close}{badge_p}")
                                    col_c.caption(f"📅 Limite: {ativ['prazo']}")

                                    if not is_concluido:
                                        with col_c.popover("⏳ Prorrogar"):
                                            nova_dt = st.date_input("Nova Data", key=f"new_dt_{ativ['id']}_{idx_a}")
                                            nova_hr = st.time_input("Nova Hora", key=f"new_hr_{ativ['id']}_{idx_a}")
                                            motivo_p = st.text_input("Motivo (Opcional)", key=f"mot_p_{ativ['id']}_{idx_a}")

                                            if st.button("Confirmar Nova Data", key=f"btn_p_{ativ['id']}_{idx_a}", use_container_width=True):
                                                for item in projeto['checklist']:
                                                    if item['id'] == ativ['id']:
                                                        prazo_antigo = item['prazo']
                                                        item.setdefault('historico_prazos', []).append({
                                                            "de": prazo_antigo,
                                                            "motivo": motivo_p,
                                                            "data_alteracao": datetime.now().strftime("%d/%m/%Y %H:%M")
                                                        })
                                                        item['prazo'] = f"{nova_dt.strftime('%d/%m/%Y')} {nova_hr.strftime('%H:%M')}"
                                                        item['prorrogacoes'] = item.get('prorrogacoes', 0) + 1
                                                        projeto['notas'].append({
                                                            "motivo": "Prorrogação de Prazo",
                                                            "depto": "PQI",
                                                            "texto": f"Atividade '{item['tarefa']}' adiada de {prazo_antigo} para {item['prazo']}. Motivo: {motivo_p}",
                                                            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                            "fase_origem": projeto['fase']
                                                        })
                                                        break
                                                salvar_seguro()
                                                st.success("Prazo prorrogado!")
                                                st.rerun()
                        else:
                            st.info("Nenhuma atividade cadastrada para esta fase.")

                    with col_e2:
                        st.markdown("#### ⚙️ Controle")

                        # FIX 9: alerta ao avançar com checklist incompleto
                        atividades_pendentes = [
                            a for a in projeto.get('checklist', [])
                            if a.get('fase_origem') == projeto['fase'] and a.get('status') != "Concluído"
                        ]
                        if atividades_pendentes:
                            st.warning(f"⚠️ {len(atividades_pendentes)} atividade(s) pendente(s) nesta fase.")

                        if st.button("▶️ AVANÇAR", use_container_width=True, type="primary") and projeto['fase'] < 8:
                            projeto['fase'] += 1
                            salvar_seguro()
                            st.rerun()
                        if st.button("⏪ RECUAR", use_container_width=True) and projeto['fase'] > 1:
                            projeto['fase'] -= 1
                            salvar_seguro()
                            st.rerun()

                        st.markdown("#### ⏰ Lembretes")
                        for l_idx, l in enumerate(projeto.get('lembretes', [])):
                            with st.container(border=True):
                                st.caption(f"📅 {l['data_hora']}")
                                st.write(l['texto'])
                                if st.button("Concluir", key=f"done_pqi_{l.get('id', l_idx)}"):
                                    projeto['lembretes'].pop(l_idx)
                                    salvar_seguro()
                                    st.rerun()

                # =====================================================
                with t_dossie:
                    sub_dos1, sub_dos2 = st.tabs(["📂 Pastas", "📜 Histórico"])

                    with sub_dos1:
                        with st.popover("➕ Criar Pasta"):
                            nome_pasta = st.text_input("Nome da Pasta")
                            if st.button("Salvar Pasta"):
                                if nome_pasta:
                                    projeto.setdefault('pastas_virtuais', {})[nome_pasta] = []
                                    salvar_seguro()
                                    st.rerun()
                                else:
                                    st.warning("Informe um nome para a pasta.")

                        pastas = projeto.get('pastas_virtuais', {})
                        for p_nome in list(pastas.keys()):
                            with st.expander(f"📁 {p_nome}"):
                                col_p1, col_p2 = st.columns([3, 1])
                                if col_p2.button("🗑️ Excluir Pasta", key=f"d_{p_nome}"):
                                    del pastas[p_nome]
                                    salvar_seguro()
                                    st.rerun()

                                up_files = st.file_uploader("Anexar (Máx 1MB)", accept_multiple_files=True, key=f"u_{p_nome}")

                                if st.button("Subir para o Banco", key=f"b_{p_nome}"):
                                    for a in up_files:
                                        tamanho_mb = a.size / (1024 * 1024)
                                        if tamanho_mb > 1.0:
                                            st.error(f"Arquivo {a.name} é muito grande ({tamanho_mb:.2f}MB). Limite: 1MB.")
                                            continue
                                        file_id = f"{datetime.now().timestamp()}_{a.name}"
                                        sucesso = db.salvar_arquivo_firestore(file_id, a.getvalue())
                                        if sucesso:
                                            pastas[p_nome].append({
                                                "nome": a.name,
                                                "file_id": file_id,
                                                "data": datetime.now().strftime("%d/%m/%Y")
                                            })
                                    salvar_seguro()
                                    st.success("Arquivos sincronizados!")
                                    st.rerun()

                                st.write("---")
                                for idx, arq in enumerate(pastas[p_nome]):
                                    c_arq1, c_arq2 = st.columns([4, 1])
                                    c_arq1.write(f"📄 {arq['nome']} ({arq['data']})")
                                    if c_arq2.button("📥 Preparar", key=f"prep_{p_nome}_{idx}"):
                                        conteudo = db.baixar_arquivo_firestore(arq['file_id'])
                                        if conteudo:
                                            st.download_button(
                                                label="Baixar Agora",
                                                data=conteudo,
                                                file_name=arq['nome'],
                                                mime="application/octet-stream",
                                                key=f"final_dl_{p_nome}_{idx}"
                                            )
                                        else:
                                            st.error("Arquivo não encontrado no banco.")

                    with sub_dos2:
                        df_hist = pd.DataFrame(projeto.get('notas', []))
                        if not df_hist.empty:
                            st.dataframe(df_hist, use_container_width=True, hide_index=True)
                        else:
                            st.info("Nenhum registro histórico encontrado.")

                # =====================================================
                with t_esforco:
                    df_esf = pd.DataFrame(projeto.get('notas', []))
                    if not df_esf.empty:
                        st.markdown(f"### Análise: {projeto['titulo']}")
                        fig = px.pie(
                            df_esf['motivo'].value_counts().reset_index(),
                            values='count', names='motivo', hole=0.4
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # FIX 10: gráfico de esforço por departamento
                        if 'depto' in df_esf.columns:
                            st.markdown("#### Ações por Departamento")
                            fig_depto = px.bar(
                                df_esf['depto'].value_counts().reset_index(),
                                x='depto', y='count',
                                labels={'depto': 'Departamento', 'count': 'Ações'},
                                color_discrete_sequence=['#002366']
                            )
                            st.plotly_chart(fig_depto, use_container_width=True)
                    else:
                        st.info("Nenhum dado de esforço registrado.")
            else:
                st.info("Nenhum projeto com este status.")
