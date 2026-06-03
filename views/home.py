import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime
from modulos.utils_tempo import agora_br, agora_iso, parse_dt_safe
from modulos import database as db

# ── Importa o módulo de Diário de Trocas ─────────────────────────────────────
try:
    from modulos import mod_diario_de_bordo
    HAS_DIARIO_TROCAS = True
except ImportError:
    try:
        import mod_diario_de_bordo
        HAS_DIARIO_TROCAS = True
    except ImportError:
        HAS_DIARIO_TROCAS = False


# ── Configurações do BI ───────────────────────────────────────────────────────
BI_BASE_URL   = "http://172.20.33.88/bi"
BI_INDEX_PAGE = "index.php"

# Mapeamento de páginas disponíveis no BI.
# Adicione novas entradas aqui sempre que surgir uma nova página no sistema.
BI_PAGINAS = {
    "🏠 Dashboard Principal":  "index.php",
    "📊 Grupo 2":              "grupo2.php",
    "🖥️ Monitor Grupo 2":      "monitorg2.php",
    # ── adicione novas páginas abaixo, sem alterar o resto do código ──────────
    # "📦 Estoque":            "estoque.php",
    # "💰 Financeiro":         "financeiro.php",
}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

def formatar_duracao_h_min(minutos):
    if pd.isna(minutos) or minutos <= 0:
        return "0min"
    horas = int(minutos // 60)
    mins  = int(minutos % 60)
    return f"{horas}H:{mins:02d}min" if horas > 0 else f"{mins}min"


def finalizar_atividade_atual(nome_usuario):
    logs  = db.carregar_esforco()
    mudou = False
    agora = agora_br()
    for idx, act in enumerate(logs):
        if act['usuario'] == nome_usuario and act['status'] == 'Em andamento':
            logs[idx]['fim']         = agora.isoformat()
            logs[idx]['status']      = 'Finalizado'
            inicio_dt                = parse_dt_safe(act.get('inicio'))
            duracao                  = (agora - inicio_dt).total_seconds() / 60
            logs[idx]['duracao_min'] = round(duracao, 2)
            mudou = True
    if mudou:
        db.salvar_esforco(logs)


# ══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def exibir(user_info):

    # ── Estilos globais ───────────────────────────────────────────────────────
    st.markdown("""
        <style>
        .reminder-card, .diary-card {
            background: #ffffff; padding: 16px; border-radius: 12px;
            margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            border-left: 6px solid;
        }
        .reminder-card { border-left-color: #ef4444; }
        .diary-card    { border-left-color: #3b82f6; }
        .status-tag    { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }

        /* ── BI nav pills ────────────────────────────────────────────────── */
        .bi-nav-container {
            display: flex; flex-wrap: wrap; gap: 8px;
            padding: 12px 0 16px;
        }
        .bi-pill {
            background: #fff; border: 1.5px solid #e2e8f0;
            border-radius: 20px; padding: 6px 16px;
            font-size: 13px; font-weight: 600; color: #475569;
            cursor: pointer; transition: all 0.2s;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        .bi-pill:hover   { border-color: #0d2145; color: #0d2145; background: #f8faff; }
        .bi-pill.active  {
            background: linear-gradient(135deg,#0d2145,#1a3a6e);
            color: #FFD700; border-color: transparent;
            box-shadow: 0 3px 10px rgba(13,33,69,0.3);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title(f"Olá, {user_info['nome']}! 👋")

    # ── Carga de dados ────────────────────────────────────────────────────────
    projs          = db.carregar_projetos()
    diario         = db.carregar_diario()
    atividades_log = db.carregar_esforco()
    motivos_gestao = db.carregar_motivos()
    hoje_dt        = agora_br().date()

    # ── Definição das abas ────────────────────────────────────────────────────
    lista_abas = [
        "⚡ Esforço Hoje",
        "🚀 Pendências",
        "📅 Agenda",
        "➕ Novo",
        "📓 Diário de Trocas",
        "👤 Perfil",
        "📊 BI King Star",
    ]

    (
        tab_esforco,
        tab_pendentes,
        tab_agenda,
        tab_novo,
        tab_diario_trocas,
        tab_perfil,
        tab_bi,
    ) = st.tabs(lista_abas)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 1 — ESFORÇO HOJE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_esforco:
        atv_ativa = next(
            (a for a in atividades_log
             if a['usuario'] == user_info['nome'] and a['status'] == 'Em andamento'),
            None
        )
        c1, c2 = st.columns([1, 1.2])

        with c1:
            if atv_ativa:
                st.info(f"🚀 **Ativo agora:**\n\n**{atv_ativa['motivo']}**")
                try:
                    inicio_dt = parse_dt_safe(atv_ativa.get('inicio'))
                    if inicio_dt:
                        decorrido = int((agora_br() - inicio_dt).total_seconds() // 60)
                        st.caption(f"Iniciado às {inicio_dt.strftime('%H:%M')} ({decorrido} min decorridos)")
                    else:
                        st.caption("Iniciado agora")
                except Exception:
                    st.caption("Erro ao calcular tempo da atividade")

                if st.button("🏁 FINALIZAR TAREFA", type="secondary", use_container_width=True):
                    finalizar_atividade_atual(user_info['nome'])
                    st.rerun()
            else:
                st.success("✨ Você está livre no momento!")

        with c2:
            with st.expander("Iniciar nova atividade", expanded=not atv_ativa):
                motivo_sel = st.selectbox("Categoria:", motivos_gestao)
                detalhes   = st.text_input("Observação ou Ticket:")

                usar_horario_manual = st.checkbox("⏰ Ajustar horário de início manualmente")
                if usar_horario_manual:
                    col_h, col_m = st.columns(2)
                    hora_manual = col_h.number_input("Hora",   0, 23, value=agora_br().hour)
                    min_manual  = col_m.number_input("Minuto", 0, 59, value=agora_br().minute)

                if st.button("INICIAR AGORA ⚡", type="primary", use_container_width=True):
                    finalizar_atividade_atual(user_info['nome'])
                    inicio_ref = (
                        agora_br().replace(hour=int(hora_manual), minute=int(min_manual), second=0)
                        if usar_horario_manual else agora_br()
                    )
                    atividades_log.append({
                        "usuario":     user_info['nome'],
                        "motivo":      motivo_sel,
                        "detalhes":    detalhes,
                        "inicio":      inicio_ref.isoformat(),
                        "fim":         None,
                        "status":      "Em andamento",
                        "duracao_min": 0,
                    })
                    db.salvar_esforco(atividades_log)
                    st.rerun()

        st.subheader("Histórico de Hoje")
        meu_hist = [a for a in atividades_log if a['usuario'] == user_info['nome']]
        if meu_hist:
            df_meu = pd.DataFrame(meu_hist)
            df_meu['inicio_dt'] = df_meu['inicio'].apply(parse_dt_safe)
            df_meu = df_meu[df_meu['inicio_dt'].apply(
                lambda x: x.date() == hoje_dt if x is not None else False
            )].sort_values('inicio_dt', ascending=False)

            if not df_meu.empty:
                df_meu['Hora']  = df_meu['inicio_dt'].dt.strftime('%H:%M')
                df_meu['Tempo'] = df_meu['duracao_min'].apply(formatar_duracao_h_min)
                st.dataframe(
                    df_meu[['Hora', 'motivo', 'detalhes', 'status', 'Tempo']],
                    use_container_width=True, hide_index=True
                )

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 2 — PENDÊNCIAS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_pendentes:
        tipo_pnd = st.radio("Filtro visual:", ["Minhas Pendências", "Visão Equipe"], horizontal=True)
        col_pqi, col_dir = st.columns(2)

        with col_pqi:
            st.subheader("📌 Processos (PQI)")
            for p_idx, p in enumerate(projs):
                lembretes = p.get('lembretes', [])
                for l_idx in range(len(lembretes) - 1, -1, -1):
                    l = lembretes[l_idx]
                    try:
                        data_l_dt = datetime.strptime(l['data_hora'].split(" ")[0], "%d/%m/%Y").date()
                        if data_l_dt <= hoje_dt:
                            atrasado = data_l_dt < hoje_dt
                            cor = "#f87171" if atrasado else "#ef4444"
                            st.markdown(f'''
                                <div class="reminder-card" style="border-left-color:{cor};">
                                    <span class="status-tag" style="color:{cor};">
                                        {"⚠️ Atrasada" if atrasado else "⏰ Hoje"}
                                    </span><br>
                                    <strong>{p["titulo"]}</strong><br>{l["texto"]}
                                </div>
                            ''', unsafe_allow_html=True)
                            if st.button(f"Concluir", key=f"btn_pqi_{p_idx}_{l_idx}", use_container_width=True):
                                p['lembretes'].pop(l_idx)
                                db.salvar_projetos(projs)
                                st.rerun()
                    except Exception:
                        continue

        with col_dir:
            st.subheader("📓 Diário de Bordo")
            for idx, sit in enumerate(diario):
                if sit.get('status') == "Pendente" and sit.get('lembrete') != "N/A":
                    if tipo_pnd == "Minhas Pendências" and sit.get('usuario') != user_info['nome']:
                        continue
                    try:
                        data_s_dt = datetime.strptime(sit['lembrete'].split(" ")[0], "%d/%m/%Y").date()
                        if data_s_dt <= hoje_dt:
                            atrasado = data_s_dt < hoje_dt
                            st.markdown(f'''
                                <div class="diary-card">
                                    <span class="status-tag" style="color:{'#ef4444' if atrasado else '#3b82f6'};">
                                        {"🚨 Atrasado" if atrasado else "📅 Agendado"}
                                    </span><br>
                                    <strong>{sit["depto"]}:</strong> {sit["solicitacao"]}<br>
                                    <small>Resp: {sit.get('usuario', 'S/I')}</small>
                                </div>
                            ''', unsafe_allow_html=True)
                            if st.button(f"Concluir", key=f"btn_dir_{idx}", use_container_width=True):
                                sit['status'] = "Executado"
                                db.salvar_diario(diario)
                                st.rerun()
                    except Exception:
                        continue

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 3 — AGENDA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_agenda:
        tipo_age  = st.radio("Visualizar compromissos de:", ["Apenas Meus", "Toda a Equipe"], horizontal=True)
        agenda_raw = []

        for sit in diario:
            if sit.get('status') == "Pendente" and sit.get('lembrete', "N/A") != "N/A":
                try:
                    data_dt = datetime.strptime(sit['lembrete'].split(" ")[0], "%d/%m/%Y").date()
                    dono    = sit.get('usuario', 'S/I')
                    if tipo_age == "Apenas Meus" and dono != user_info['nome']:
                        continue
                    if data_dt > hoje_dt:
                        agenda_raw.append({
                            "Data_Ref": data_dt,
                            "Data":     data_dt.strftime("%d/%m/%Y"),
                            "Origem":   f"Diário ({sit['depto']})",
                            "Tarefa":   sit['solicitacao'],
                            "Quem":     dono,
                        })
                except Exception:
                    continue

        for p in projs:
            for l in p.get('lembretes', []):
                try:
                    data_dt = datetime.strptime(l['data_hora'].split(" ")[0], "%d/%m/%Y").date()
                    if data_dt > hoje_dt:
                        agenda_raw.append({
                            "Data_Ref": data_dt,
                            "Data":     data_dt.strftime("%d/%m/%Y"),
                            "Origem":   f"PQI: {p['titulo']}",
                            "Tarefa":   l['texto'],
                            "Quem":     "Equipe",
                        })
                except Exception:
                    continue

        if agenda_raw:
            df_age = pd.DataFrame(agenda_raw).sort_values(by="Data_Ref")
            st.dataframe(df_age[['Data', 'Origem', 'Tarefa', 'Quem']], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum compromisso futuro encontrado.")

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 4 — NOVO AGENDAMENTO
    # ══════════════════════════════════════════════════════════════════════════
    with tab_novo:
        st.subheader("🎯 Criar Novo Lembrete")
        with st.form("form_novo_v2"):
            tipo = st.selectbox("Vincular a:", ["Situações Diárias (Diário)", "Processos (PQI)"])
            txt_lembrete = st.text_area("O que precisa ser feito?", placeholder="Descreva a tarefa...")

            c1, c2  = st.columns(2)
            d_agendada = c1.date_input("Para quando?", min_value=hoje_dt)
            h_agendada = c2.time_input("Qual horário?", value=datetime.now().time())

            proj_vinc = None
            if tipo == "Processos (PQI)":
                proj_vinc = st.selectbox("Selecione o Projeto PQI:", [p['titulo'] for p in projs])

            if st.form_submit_button("AGENDAR TAREFA 🚀", use_container_width=True):
                if not txt_lembrete:
                    st.error("Por favor, descreva a tarefa.")
                else:
                    data_f = f"{d_agendada.strftime('%d/%m/%Y')} {h_agendada.strftime('%H:%M')}"
                    if tipo == "Processos (PQI)":
                        for p in projs:
                            if p['titulo'] == proj_vinc:
                                p.setdefault('lembretes', []).append({
                                    "id":       datetime.now().timestamp(),
                                    "data_hora": data_f,
                                    "texto":    txt_lembrete,
                                    "status":   "Pendente",
                                })
                        db.salvar_projetos(projs)
                    else:
                        diario.append({
                            "usuario":    user_info['nome'],
                            "data_reg":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "solicitacao": txt_lembrete,
                            "depto":      "GERAL",
                            "lembrete":   data_f,
                            "status":     "Pendente",
                        })
                        db.salvar_diario(diario)

                    st.success(f"Tarefa agendada para {data_f}!")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 5 — DIÁRIO DE TROCAS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_diario_trocas:
        if HAS_DIARIO_TROCAS:
            mod_diario_de_bordo.exibir(user_info)
        else:
            st.error(
                "⚠️ Módulo **mod_diario_de_bordo** não encontrado.\n\n"
                "Certifique-se de que o arquivo `mod_diario_de_bordo.py` está em `modulos/`."
            )

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 6 — PERFIL
    # ══════════════════════════════════════════════════════════════════════════
    with tab_perfil:
        st.subheader("👤 Meu Perfil")

        foto = st.file_uploader("Escolha uma foto", type=["png", "jpg", "jpeg"])
        if foto is not None:
            import os
            os.makedirs("fotos", exist_ok=True)
            caminho = f"fotos/{user_info['nome']}.png"
            with open(caminho, "wb") as f:
                f.write(foto.getbuffer())
            st.success("Foto salva com sucesso!")

        try:
            st.image(f"fotos/{user_info['nome']}.png", width=150)
        except Exception:
            st.info("Você ainda não possui foto.")

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 7 — BI KING STAR  (navegação interna completa)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_bi:
        st.subheader("📊 BI — King Star Colchões")

        # ── Seletor de página ─────────────────────────────────────────────────
        # Mantém a página selecionada no session_state para não resetar ao
        # interagir com outros widgets da home.
        if "bi_pagina_sel" not in st.session_state:
            st.session_state["bi_pagina_sel"] = BI_INDEX_PAGE

        col_nav, col_link = st.columns([3, 1])

        with col_nav:
            # Radio horizontal com as páginas mapeadas
            rotulos  = list(BI_PAGINAS.keys())
            arquivos = list(BI_PAGINAS.values())

            # Descobre o índice atual para manter a seleção
            try:
                idx_atual = arquivos.index(st.session_state["bi_pagina_sel"])
            except ValueError:
                idx_atual = 0

            escolha_rotulo = st.radio(
                "Página do BI:",
                rotulos,
                index=idx_atual,
                horizontal=True,
                key="bi_radio_pagina",
                label_visibility="collapsed",
            )
            pagina_arquivo = BI_PAGINAS[escolha_rotulo]
            st.session_state["bi_pagina_sel"] = pagina_arquivo

        url_completa = f"{BI_BASE_URL}/{pagina_arquivo}"

        with col_link:
            st.markdown(
                f"<br><a href='{url_completa}' target='_blank' "
                f"style='font-size:13px;font-weight:600;color:#0d2145;text-decoration:none;'>"
                f"↗️ Abrir em nova guia</a>",
                unsafe_allow_html=True,
            )

        st.caption(f"🔗 {url_completa}")
        st.divider()

        # ── Iframe que acompanha a página selecionada ─────────────────────────
        # height=820 dá espaço generoso; ajuste se necessário.
        components.iframe(url_completa, height=820, scrolling=True)

        # ── Dica de uso ───────────────────────────────────────────────────────
        with st.expander("ℹ️ Como adicionar novas páginas do BI"):
            st.markdown("""
            Abra o arquivo **`views/home.py`** (ou onde este módulo estiver salvo)
            e localize o dicionário `BI_PAGINAS` no início do arquivo:

            ```python
            BI_PAGINAS = {
                "🏠 Dashboard Principal":  "index.php",
                "📊 Grupo 2":              "grupo2.php",
                "🖥️ Monitor Grupo 2":      "monitorg2.php",
                # adicione abaixo:
                "📦 Estoque":              "estoque.php",
            }
            ```

            Basta adicionar uma nova linha com o **nome que aparecerá no botão**
            e o **nome do arquivo `.php`** correspondente.  
            Nenhuma outra alteração no código é necessária.
            """)
